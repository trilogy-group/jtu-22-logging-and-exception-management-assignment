from http.client import HTTPException
import time
import uuid
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")

filehandler = logging.FileHandler('routers.log')
filehandler.setFormatter(formatter)

logger.addHandler(filehandler)

from datetime import datetime
from fastapi import APIRouter
from fastapi import Request, Depends
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

@router.post("/submit/")
async def submit(file: Request, apikey: APIKey = Depends(get_api_key)):
    start = int(time.time() * 1000.0)
    t1 = [int(time.time() * 1000.0)]
    
    if not db_helper_session.verify_api_key(apikey):
        raise HTTPException(status_code=401, detail="User unauthorized")
    
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
        logger.error('Error occured while parsing XML')
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
        logger.error("Validation failed: adf xml")
        return {
            "status": "REJECTED",
            "code": validation_code,
            "message": validation_message
        }
    else:
        logger.info("adf xml validated")

    # check if vendor is available here
    dealer_available = True if obj['adf']['prospect'].get('vendor', None) else False
    email, phone, last_name = get_contact_details(obj)
    make = obj['adf']['prospect']['vehicle']['make']
    model = obj['adf']['prospect']['vehicle']['model']

    logger.info(dealer_available ? "Dealer(s) available" : "No dealer is available")

    fetched_oem_data = {}

    # check if 3PL is making a duplicate call or it is a duplicate lead
    with ThreadPoolExecutor(max_workers=5) as executor:
        logger.info("A new call initiated")
        start = int(time.time() * 1000.0)
        futures = [executor.submit(db_helper_session.check_duplicate_api_call, lead_hash,
                                   obj['adf']['prospect']['provider']['service']),
                   executor.submit(db_helper_session.check_duplicate_lead, email, phone, last_name, make, model),
                   executor.submit(db_helper_session.fetch_oem_data, make, True)
                   ]
        for future in as_completed(futures):
            result = future.result()
            if result.get('Duplicate_Api_Call', {}).get('status', False):
                end = int(time.time() * 1000.0)
                logger.warning(f"Duplicate api call found: {end-start}ms")
                return {
                    "status": f"Already {result['Duplicate_Api_Call']['response']}",
                    "message": "Duplicate Api Call"
                }
            if result.get('Duplicate_Lead', False):
                end = int(time.time() * 1000.0)
                logger.warning(f"Duplicate lead found: {int(time.time() * 1000.0)-start}ms")
                return {
                    "status": "REJECTED",
                    "code": "12_DUPLICATE",
                    "message": "This is a duplicate lead"
                }
            if "fetch_oem_data" in result:
                fetched_oem_data = result['fetch_oem_data']
        end = int(time.time() * 1000.0)
        logger.info(f"Call executed: {end-start}ms")
        logger.info(f"Fetched data : {fetched_oem_data}")
    if fetched_oem_data == {}:
        logger.error("OEM data not found")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    if 'threshold' not in fetched_oem_data:
        logger.error("OEM data not found")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    oem_threshold = float(fetched_oem_data['threshold'])
    logger.info(f"OEM threshold fetchted: {oem_threshold}")

    # if dealer is not available then find nearest dealer
    if not dealer_available:
        logger.info("Dealer not available, finding the nearest dealer")
        lat, lon = get_customer_coordinate(obj['adf']['prospect']['customer']['contact']['address']['postalcode'])
        nearest_vendor = db_helper_session.fetch_nearest_dealer(oem=make,
                                                                lat=lat,
                                                                lon=lon)
        obj['adf']['prospect']['vendor'] = nearest_vendor
        dealer_available = True if nearest_vendor != {} else False
        logger.info(dealer_available ? f"A dealer is found: {nearest_vendor}" : "No nearby dealer found")

    logger.info("Initiating calculation of lead score")
    start = int(time.time() * 1000.0)
    
    # enrich the lead
    model_input = get_enriched_lead_json(obj)

    # convert the enriched lead to ML input format
    ml_input = conversion_to_ml_input(model_input, make, dealer_available)

    # score the lead
    result = score_ml_input(ml_input, make, dealer_available)

    end = int(time.time() * 1000.0)
    logger.info(f"Lead score calculated: {result} : {end-start}ms")

    # create the response
    response_body = {}
    if result >= oem_threshold:
        response_body["status"] = "ACCEPTED"
        response_body["code"] = "0_ACCEPTED"
    else:
        response_body["status"] = "REJECTED"
        response_body["code"] = "16_LOW_SCORE"
    logger.info(f"Response created : {response_body}")

    # verify the customer
    if response_body['status'] == 'ACCEPTED':
        contact_verified = await new_verify_phone_and_email(email, phone)
        if not contact_verified:
            logger.warning("Customer not verified")
            response_body['status'] = 'REJECTED'
            response_body['code'] = '17_FAILED_CONTACT_VALIDATION'
        else:
            logger.info("Customer verified")

    lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, email + phone + last_name + make + model))
    item, path = create_quicksight_data(obj['adf']['prospect'], lead_uuid, response_body['status'],
                                        response_body['code'], model_input)
    # insert the lead into ddb with oem & customer details
    # delegate inserts to sqs queue
    if response_body['status'] == 'ACCEPTED':
        logger.info("Intialising insertion of the lead into db")
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
        logger.info("Lead inserted into db")

    else:
        logger.info("Respnse body not accepted")
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
    time_taken = (int(time.time() * 1000.0) - t1)

    response_message = f"{result} Response Time : {time_taken} ms"

    logger.info(response_message)

    return response_body
