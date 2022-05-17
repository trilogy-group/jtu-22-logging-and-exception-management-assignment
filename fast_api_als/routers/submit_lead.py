import time
import uuid
import logging

from datetime import datetime
from fastapi import APIRouter
from fastapi import Request, Depends
from fastapi.security.api_key import APIKey
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import HTTPException

from fast_api_als.services.authenticate import get_api_key
from fast_api_als.services.enrich.customer_info import get_contact_details
from fast_api_als.services.enrich.demographic_data import get_customer_coordinate
from fast_api_als.services.enrich_lead import get_enriched_lead_json
from fast_api_als.services.new_verify_phone_and_email import new_verify_phone_and_email
from fast_api_als.utils.adf import parse_xml, check_validation
from fast_api_als.utils.calculate_lead_hash import calculate_lead_hash
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.ml_helper import conversion_to_ml_input, score_ml_input
from fast_api_als.utils.quicksight_utils import create_quicksight_data
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.utils.sqs_utils import sqs_helper_session

router = APIRouter()

"""
Add proper logging and exception handling.

keep in mind:
You as a developer has to find how much time each part of code takes.
you will get the idea about the part when you go through the code.
"""

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

@router.post("/submit/")
async def submit(file: Request, apikey: APIKey = Depends(get_api_key)):
    start = int(time.time() * 1000.0)
    t1 = [int(time.time() * 1000.0)]
    
    logging.info("Verifying API KEY")
    if not db_helper_session.verify_api_key(apikey):
        # throw proper fastpi.HTTPException
        logging.error("API Key not valid")
        time_taken = (int(time.time() * 1000.0) - start)
        logging.info(f"API Key Error Submit Request Failed in {time_taken}ms"
        raise HTTPException(status_code=401, detail="API key not valid")
        # pass
    
    body = await file.body()
    body = str(body, 'utf-8')

    obj = parse_xml(body)
    logging.info(f"Parsed Body, obj -> {obj}")

    
    # check if xml was not parsable, if not return
    if not obj:
        logging.info("Imparsable XML")
        logging.info("Fetching API Key")
        provider = db_helper_session.get_api_key_author(apikey)
        obj = {
            'provider': {
                'service': provider
            }
        }
        logging.info("Creating QuickSight Data")
        item, path = create_quicksight_data(obj, 'unknown_hash', 'REJECTED', '1_INVALID_XML', {})
        upload_start = int(time.time() * 1000.0)
        s3_helper_client.put_file(item, path)
        upload_tt = int(time.time() * 1000.0) - upload_start
        logging.info(f"Data Uploaded [{upload_tt}]")
        time_taken = (int(time.time() * 1000.0) - start)
        logging.info(f"Invalid XMl Submit Request Rejected in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "1_INVALID_XML",
            "message": "Error occured while parsing XML"
        }

    logging.info("Calculating Lead Hash")
    lead_hash = calculate_lead_hash(obj)
    logging.info(f"Lead hash caluclated, lead hash -> {lead_hash}")

    logging.info("Checking Adf validation")
    # check if adf xml is valid
    validation_check, validation_code, validation_message = check_validation(obj)
    logging.inof(f"Validated adf xml , validation_check -> {validation_check}")

    #if not valid return
    if not validation_check:
        logging.info("Adf Invalid")
        logging.info("Creating Quick Sight Data")
        item, path = create_quicksight_data(obj['adf']['prospect'], lead_hash, 'REJECTED', validation_code, {})
        logging.info("Uploading Data to s3")
        upload_start = int(time.time() * 1000.0)
        s3_helper_client.put_file(item, path)
        upload_tt = int(time.time() * 1000.0) - upload_start
        logging.info(f"Data Uploaded in {upload_tt}ms")
        time_taken = (int(time.time() * 1000.0) - start)
        logging.info(f"Validation Failed Submit Request Rejected [{time_taken}ms]")
        return {
            "status": "REJECTED",
            "code": validation_code,
            "message": validation_message
        }
    logging.info(f"Adf validation check done, obj-> {obj}")

    # check if vendor is available here
    dealer_available = True if obj['adf']['prospect'].get('vendor', None) else False
    logging.info("Getting Contact Details")
    email, phone, last_name = get_contact_details(obj)
    make = obj['adf']['prospect']['vehicle']['make']
    model = obj['adf']['prospect']['vehicle']['model']


    fetched_oem_data = {}

    # check if 3PL is making a duplicate call or it is a duplicate lead
    with ThreadPoolExecutor(max_workers=5) as executor:
        logging.info("Thread executor futures")
        futures = [executor.submit(db_helper_session.check_duplicate_api_call, lead_hash,
                                   obj['adf']['prospect']['provider']['service']),
                   executor.submit(db_helper_session.check_duplicate_lead, email, phone, last_name, make, model),
                   executor.submit(db_helper_session.fetch_oem_data, make, True)
                   ]
        for future in as_completed(futures):
            result = future.result()
            if result.get('Duplicate_Api_Call', {}).get('status', False):
                time_taken = (int(time.time() * 1000.0) - start)
                logging.info(f"Duplicate API Call Submit Request Exited in {time_taken}ms")
                return {
                    "status": f"Already {result['Duplicate_Api_Call']['response']}",
                    "message": "Duplicate Api Call"
                }
            if result.get('Duplicate_Lead', False):
                time_taken = (int(time.time() * 1000.0) - start)
                logging.info(f"Duplicate Lead Submit Request Exited in {time_taken}ms")
                return {
                    "status": "REJECTED",
                    "code": "12_DUPLICATE",
                    "message": "This is a duplicate lead"
                }
            if "fetch_oem_data" in result:
                fetched_oem_data = result['fetch_oem_data']
    if fetched_oem_data == {}:
        time_taken = (int(time.time() * 1000.0) - start)
        logging.info(f"OEM data empty Submit Request Rejected in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    if 'threshold' not in fetched_oem_data:
        time_taken = (int(time.time() * 1000.0) - start)
        logging.info(f"OEM threshold not present Submit Request Rejected in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    oem_threshold = float(fetched_oem_data['threshold'])

    # if dealer is not available then find nearest dealer
    if not dealer_available:
        logging.info("Fetching nearest dealer")
        lat, lon = get_customer_coordinate(obj['adf']['prospect']['customer']['contact']['address']['postalcode'])
        nearest_vendor = db_helper_session.fetch_nearest_dealer(oem=make,
                                                                lat=lat,
                                                                lon=lon)
        logging.info(f"Fetched nearest vendor {nearest_vendor}")
        obj['adf']['prospect']['vendor'] = nearest_vendor
        dealer_available = True if nearest_vendor != {} else False

    # enrich the lead
    logging.info("Getting Enriched Lead")
    t_start = int(time.time() * 1000.0)
    model_input = get_enriched_lead_json(obj)
    t_time_taken = int(time.time() * 1000.0) - start
    logging.info(f"Enriched Lead in {t_time_taken}ms")

    # convert the enriched lead to ML input format
    logging.info("Converting enriched lead to ML input format")
    t_start = int(time.time() * 1000.0)
    ml_input = conversion_to_ml_input(model_input, make, dealer_available)
    t_time_taken = int(time.time() * 1000.0) - start
    logging.info(f"Converted into ml input {ml_input} in {t_time_taken}ms")

    # score the lead
    logging.info("Scoring Lead")
    t_start = int(time.time() * 1000.0)
    result = score_ml_input(ml_input, make, dealer_available)
    t_time_taken = int(time.time() * 1000.0) - start
    logging.info(f"Lead Score with result {result} in {t_time_taken}ms")

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
        logging.info("Verifying Customer")
        contact_verified = await new_verify_phone_and_email(email, phone)
        logging.info(f"Customer Verified ")
        if not contact_verified:
            response_body['status'] = 'REJECTED'
            response_body['code'] = '17_FAILED_CONTACT_VALIDATION'

    lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, email + phone + last_name + make + model))
    logging.info("Creating QuickSight Data")
    item, path = create_quicksight_data(obj['adf']['prospect'], lead_uuid, response_body['status'],
                                        response_body['code'], model_input)
    # insert the lead into ddb with oem & customer details
    # delegate inserts to sqs queue
    if response_body['status'] == 'ACCEPTED':
        make_model_filter = db_helper_session.get_make_model_filter_status(make)
        logging.info("Fetched Make Model Filter")
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
    logging.info(f"Request Completed in {time_taken}ms")
    response_message = f"{result} Response Time : {time_taken} ms"

    return response_body
