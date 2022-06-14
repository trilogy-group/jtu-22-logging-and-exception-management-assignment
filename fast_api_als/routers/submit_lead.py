import time
import uuid
import logging

from datetime import datetime
from fastapi import APIRouter
from fastapi import Request, Depends, HTTPException
from fastapi.security.api_key import APIKey
from concurrent.futures import ThreadPoolExecutor, as_completed

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

logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(asctime)s:%(module)s')

@router.post("/submit/")
async def submit(file: Request, apikey: APIKey = Depends(get_api_key)):
    start = int(time.time() * 1000.0)
    t1 = time.time()
    
    if not db_helper_session.verify_api_key(apikey):
        # throw proper fastpi.HTTPException
        logging.error("Verification of API key failed")
        raise HTTPException(401,detail="Verification of Api key failed")
    
    t2=time.time()
    logging.info("Verification of Api key successful in "+ str((t2-t1)*1000)+ "ms")
    body = await file.body()
    body = str(body, 'utf-8')

    obj = parse_xml(body)

    # check if xml was not parsable, if not return
    if not obj:
        provider = db_helper_session.get_api_key_author(apikey)
        obj = {
            'provider': {
                'service': provider
            }
        }
        item, path = create_quicksight_data(obj, 'unknown_hash', 'REJECTED', '1_INVALID_XML', {})
        s3_helper_client.put_file(item, path)
        logging.error("XML not parsable")
        return {
            "status": "REJECTED",
            "code": "1_INVALID_XML",
            "message": "Error occured while parsing XML"
        }
    
    lead_hash = calculate_lead_hash(obj)

    # check if adf xml is valid
    validation_check, validation_code, validation_message = check_validation(obj)

    #if not valid return
    if not validation_check:
        item, path = create_quicksight_data(obj['adf']['prospect'], lead_hash, 'REJECTED', validation_code, {})
        s3_helper_client.put_file(item, path)
        logging.error("Validation check failed")
        return {
            "status": "REJECTED",
            "code": validation_code,
            "message": validation_message
        }
    t1=time.time()
    # check if vendor is available here
    try:
        dealer_available = True if obj['adf']['prospect'].get('vendor', None) else False
        email, phone, last_name = get_contact_details(obj)
        make = obj['adf']['prospect']['vehicle']['make']
        model = obj['adf']['prospect']['vehicle']['model']
        t2=time.time()
        logging.info("Reveived vendor details correctly in " + str((t2-t1)*1000) + "ms")
    except:
        logging.error("Didn't receive vendor details.")


    fetched_oem_data = {}

    # check if 3PL is making a duplicate call or it is a duplicate lead
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(db_helper_session.check_duplicate_api_call, lead_hash,
                                   obj['adf']['prospect']['provider']['service']),
                   executor.submit(db_helper_session.check_duplicate_lead, email, phone, last_name, make, model),
                   executor.submit(db_helper_session.fetch_oem_data, make, True)
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
    logging.info("checked if 3PL is making a duplicate call or it is a duplicate lead")

    # if dealer is not available then find nearest dealer
    if not dealer_available:
        logging.info("Dealer not available")
        lat, lon = get_customer_coordinate(obj['adf']['prospect']['customer']['contact']['address']['postalcode'])
        nearest_vendor = db_helper_session.fetch_nearest_dealer(oem=make,
                                                                lat=lat,
                                                                lon=lon)
        obj['adf']['prospect']['vendor'] = nearest_vendor
        dealer_available = True if nearest_vendor != {} else False
        logging.info("Nearest Dealer found")
    else:
        logging.info("Dealer Available")

    # enrich the lead
    model_input = get_enriched_lead_json(obj)
    logging.info("Got enriched lead_json")

    # convert the enriched lead to ML input format
    ml_input = conversion_to_ml_input(model_input, make, dealer_available)
    logging.info("Converted enriched lead to ML input format")

    # score the lead
    result = score_ml_input(ml_input, make, dealer_available)
    logging.info("Scored the lead")

    # create the response
    response_body = {}
    if result >= oem_threshold:
        response_body["status"] = "ACCEPTED"
        response_body["code"] = "0_ACCEPTED"
    else:
        response_body["status"] = "REJECTED"
        response_body["code"] = "16_LOW_SCORE"
    logging.info("Created the response")

    # verify the customer
    if response_body['status'] == 'ACCEPTED':
        contact_verified = await new_verify_phone_and_email(email, phone)
        if not contact_verified:
            response_body['status'] = 'REJECTED'
            response_body['code'] = '17_FAILED_CONTACT_VALIDATION'
    logging.info("Verified the customer")

    lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, email + phone + last_name + make + model))
    item, path = create_quicksight_data(obj['adf']['prospect'], lead_uuid, response_body['status'],
                                        response_body['code'], model_input)
    # insert the lead into ddb with oem & customer details
    # delegate inserts to sqs queue
    if response_body['status'] == 'ACCEPTED':
        make_model_filter = db_helper_session.get_make_model_filter_status(make)
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

    logging.info("inserted the lead into ddb with oem & customer details delegated inserts to sqs queue")

    response_message = f"{result} Response Time : {time_taken} ms"
    logging.info("Completed in " + {time_taken} + "ms")
    return response_body
