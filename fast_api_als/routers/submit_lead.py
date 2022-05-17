import time
import uuid
import logging

from datetime import datetime
from fastapi import APIRouter
from fastapi import Request, Depends, HTTPException
from fastapi.security.api_key import APIKey
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.authenticate import get_api_key
from services.enrich.customer_info import get_contact_details
from services.enrich.demographic_data import get_customer_coordinate
from services.enrich_lead import get_enriched_lead_json
from services.new_verify_phone_and_email import new_verify_phone_and_email
from utils.adf import parse_xml, check_validation
from utils.calculate_lead_hash import calculate_lead_hash
from database.db_helper import db_helper_session
from services.ml_helper import conversion_to_ml_input, score_ml_input
from utils.quicksight_utils import create_quicksight_data
from quicksight.s3_helper import s3_helper_client
from utils.sqs_utils import sqs_helper_session

router = APIRouter()

"""
Add proper logging and exception handling.

keep in mind:
You as a developer has to find how much time each part of code takes.
you will get the idea about the part when you go through the code.
"""


@router.post("/submit/")
async def submit(file: Request, apikey: APIKey = Depends(get_api_key)):

    start = int(time.time() * 1000.0)
    if not db_helper_session.verify_api_key(apikey):
        logging.error("[Submit File]: API key not verified")
        raise HTTPException(status_code=401, detail="API key not verified")

    body = await file.body()
    body = str(body, 'utf-8')

    now = int(time.time() * 1000.0)
    logging.info(
        f'[Submit File]: file body parsed and converted to string in {now - start}ms')

    before = int(time.time() * 1000.0)
    obj = parse_xml(body)
    now = int(time.time() * 1000.0)
    logging.info(f'[Submit File]: Body xml parsed in {now - before}ms')

    # check if xml was not parsable, if not return
    if not obj:

        before = int(time.time() * 1000.0)
        provider = db_helper_session.get_api_key_author(apikey)
        obj = {
            'provider': {
                'service': provider
            }
        }
        item, path = create_quicksight_data(
            obj, 'unknown_hash', 'REJECTED', '1_INVALID_XML', {})
        s3_helper_client.put_file(item, path)

        now = int(time.time() * 1000.0)
        logging.info(
            f'[Submit File]: Rejected response due unable to parse xml processed in {now - before}ms')

        return {
            "status": "REJECTED",
            "code": "1_INVALID_XML",
            "message": "Error occured while parsing XML"
        }

    before = int(time.time() * 1000.0)
    lead_hash = calculate_lead_hash(obj)
    now = int(time.time() * 1000.0)
    logging.info(f'[Submit File]: lead hash calculated in {now - before}ms')

    before = int(time.time() * 1000.0)
    # check if adf xml is valid
    validation_check, validation_code, validation_message = check_validation(
        obj)
    now = int(time.time() * 1000.0)
    logging.info(
        f'[Submit File]: adf xml validation check completed in {now - before}ms')

    # if not valid return
    if not validation_check:
        before = int(time.time() * 1000.0)

        item, path = create_quicksight_data(
            obj['adf']['prospect'], lead_hash, 'REJECTED', validation_code, {})
        s3_helper_client.put_file(item, path)

        now = int(time.time() * 1000.0)
        logging.info(
            f'[Submit File]: Rejected response due to adf xml validation check failure processed in {now - before}ms')

        return {
            "status": "REJECTED",
            "code": validation_code,
            "message": validation_message
        }

    # check if vendor is available here
    dealer_available = True if obj['adf']['prospect'].get(
        'vendor', None) else False
    try:
        email, phone, last_name = get_contact_details(obj)
    except:
        logging.error('[Submit File]: Unable to get contact details')
    make = obj['adf']['prospect']['vehicle']['make']
    model = obj['adf']['prospect']['vehicle']['model']

    fetched_oem_data = {}

    # check if 3PL is making a duplicate call or it is a duplicate lead
    before = int(time.time() * 1000.0)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(db_helper_session.check_duplicate_api_call, lead_hash,
                                   obj['adf']['prospect']['provider']['service']),
                   executor.submit(db_helper_session.check_duplicate_lead,
                                   email, phone, last_name, make, model),
                   executor.submit(
                       db_helper_session.fetch_oem_data, make, True)
                   ]
        for future in as_completed(futures):
            result = future.result()
            if result.get('Duplicate_Api_Call', {}).get('status', False):
                return {
                    "status": f"Already {result['Duplicate_Api_Call']['response']}",
                    "message": "Duplicate Api Call"
                }
            if result.get('Duplicate_Lead', False):
                return {
                    "status": "REJECTED",
                    "code": "12_DUPLICATE",
                    "message": "This is a duplicate lead"
                }
            if "fetch_oem_data" in result:
                fetched_oem_data = result['fetch_oem_data']
    now = int(time.time() * 1000.0)
    logging.info(
        f'[Submit File]: Duplicate call/Duplicate lead check complete in {now - before}ms')

    if fetched_oem_data == {}:
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    if 'threshold' not in fetched_oem_data:
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    oem_threshold = float(fetched_oem_data['threshold'])

    # if dealer is not available then find nearest dealer
    if not dealer_available:
        lat, lon = get_customer_coordinate(
            obj['adf']['prospect']['customer']['contact']['address']['postalcode'])
        nearest_vendor = db_helper_session.fetch_nearest_dealer(oem=make,
                                                                lat=lat,
                                                                lon=lon)
        obj['adf']['prospect']['vendor'] = nearest_vendor
        dealer_available = True if nearest_vendor != {} else False

    # enrich the lead
    before = int(time.time() * 1000.0)
    model_input = get_enriched_lead_json(obj)
    now = int(time.time() * 1000.0)
    logging.info(f'[Submit File]: Lead enriched in {now - before}ms')

    # convert the enriched lead to ML input format
    before = int(time.time() * 1000.0)
    ml_input = conversion_to_ml_input(model_input, make, dealer_available)
    now = int(time.time() * 1000.0)
    logging.info(
        f'[Submit File]: Lead converted to ml input in {now - before}ms')

    # score the lead
    before = int(time.time() * 1000.0)
    result = score_ml_input(ml_input, make, dealer_available)
    now = int(time.time() * 1000.0)
    logging.info(f'[Submit File]: Lead scored by ml in {now - before}ms')

    # create the response
    response_body = {}
    if result >= oem_threshold:
        response_body["status"] = "ACCEPTED"
        response_body["code"] = "0_ACCEPTED"
    else:
        response_body["status"] = "REJECTED"
        response_body["code"] = "16_LOW_SCORE"

    # verify the customer
    if response_body['status'] == 'ACCEPTED':
        before = int(time.time() * 1000.0)
        try:
            contact_verified = await new_verify_phone_and_email(email, phone)
        except:
            logging.error("[Submit File]: Failed to verify phone and email")
        now = int(time.time() * 1000.0)
        logging.info(
            f'[Submit File]: Phone and email verified in {now - before}ms')
        if not contact_verified:
            response_body['status'] = 'REJECTED'
            response_body['code'] = '17_FAILED_CONTACT_VALIDATION'

    lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, email +
                    phone + last_name + make + model))
    try:
        item, path = create_quicksight_data(obj['adf']['prospect'], lead_uuid, response_body['status'],
                                            response_body['code'], model_input)
    except:
        logging.error("[Submit File]: Failed to create quicksight data")
    # insert the lead into ddb with oem & customer details
    # delegate inserts to sqs queue
    if response_body['status'] == 'ACCEPTED':
        make_model_filter = db_helper_session.get_make_model_filter_status(
            make)
        message = {
            'put_file': {
                'item': item,
                'path': path
            },
            'insert_lead': {
                'lead_hash': lead_hash,
                'service': obj['adf']['prospect']['provider']['service'],
                'response': response_body['status']
            },
            'insert_oem_lead': {
                'lead_uuid': lead_uuid,
                'make': make,
                'model': model,
                'date': datetime.today().strftime('%Y-%m-%d'),
                'email': email,
                'phone': phone,
                'last_name': last_name,
                'timestamp': datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),
                'make_model_filter': make_model_filter,
                'lead_hash': lead_hash,
                'vendor': obj['adf']['prospect']['vendor'].get('vendorname', 'unknown'),
                'service': obj['adf']['prospect']['provider']['service'],
                'postalcode': obj['adf']['prospect']['customer']['contact']['address']['postalcode']
            },
            'insert_customer_lead': {
                'lead_uuid': lead_uuid,
                'email': email,
                'phone': phone,
                'last_name': last_name,
                'make': make,
                'model': model
            }
        }
        res = sqs_helper_session.send_message(message)

    else:
        message = {
            'put_file': {
                'item': item,
                'path': path
            },
            'insert_lead': {
                'lead_hash': lead_hash,
                'service': obj['adf']['prospect']['provider']['service'],
                'response': response_body['status']
            }
        }
        res = sqs_helper_session.send_message(message)
    time_taken = (int(time.time() * 1000.0) - start)
    logging.info(f'[Submit File]: Completed in {time_taken}ms')
    response_message = f"{result} Response Time : {time_taken} ms"

    return response_body
