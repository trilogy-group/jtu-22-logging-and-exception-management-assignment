import time
import uuid
from fast_api_als.utils.logger import logger

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

@router.post("/submit/")
async def submit(file: Request, apikey: APIKey = Depends(get_api_key)):
    start = int(time.time() * 1000.0)
    t1 = [int(time.time() * 1000.0)]
    
    if not db_helper_session.verify_api_key(apikey):
        logger.error("Submit request terminated: API key verification failed")
        raise HTTPException(status_code=401, detail="Invalid api key")
        pass
    
    body = await file.body()
    body = str(body, 'utf-8')

    obj = parse_xml(body)

    # check if xml was not parsable, if not return
    if not obj:
        logger.info(f"XML parsing failed for {body}")
        provider = db_helper_session.get_api_key_author(apikey)
        obj = {
            'provider': {
                'service': provider
            }
        }

        item, path = create_quicksight_data(obj, 'unknown_hash', 'REJECTED', '1_INVALID_XML', {})
        try:
            upload_start = time.time()
            s3_helper_client.put_file(item, path)
            upload_time_taken = (time.time() - upload_start) * 1000
            logger.info(f"Data uploaded in {upload_time_taken}ms")
        except Exception as e:
            logger.error(f"Error occurred while uploading item to S3: {e.message}")
        time_taken = (time.time() - start_time) * 1000
        logger.info(f"Submit request completed in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "1_INVALID_XML",
            "message": "Error occured while parsing XML"
        }
    
    logger.info("Calculating lead hash")
    lead_hash = calculate_lead_hash(obj)
    logger.info(f"Lead hash for data: {lead_hash}")

    logger.info("Validating adf xml")
    # check if adf xml is valid
    validation_check, validation_code, validation_message = check_validation(obj)

    #if not valid return
    if not validation_check:
        logger.info("adf xml is invalid")
        item, path = create_quicksight_data(obj['adf']['prospect'], lead_hash, 'REJECTED', validation_code, {})
        try:
            upload_start = time.time()
            s3_helper_client.put_file(item, path)
            upload_time_taken = (time.time() - upload_start) * 1000
            logger.info(f"Data uploaded in {upload_time_taken}ms")
        except Exception as e:
            logger.error(f"Error occurred while uploading item to S3: {e.message}")
        time_taken = (time.time() - start_time) * 1000
        logger.info(f"Submit request completed for data in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": validation_code,
            "message": validation_message
        }

    # check if vendor is available here
    
    logger.info("Checking for vendor availability")

    dealer_available = True if obj['adf']['prospect'].get('vendor', None) else False
    email, phone, last_name = get_contact_details(obj)
    make = obj['adf']['prospect']['vehicle']['make']
    model = obj['adf']['prospect']['vehicle']['model']

    fetched_oem_data = {}

    # check if 3PL is making a duplicate call or it is a duplicate lead
    logger.info("Checking for duplicate calls or leads by 3PL")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(db_helper_session.check_duplicate_api_call, lead_hash,
                                   obj['adf']['prospect']['provider']['service']),
                   executor.submit(db_helper_session.check_duplicate_lead, email, phone, last_name, make, model),
                   executor.submit(db_helper_session.fetch_oem_data, make, True)
                   ]
        for future in as_completed(futures):
            result = future.result()
            if result.get('Duplicate_Api_Call', {}).get('status', False):
                logger.info("Duplicate API call found")
                time_taken = (time.time() - start_time) * 1000
                logger.info(f"Submit request completed for data in {time_taken}ms")
                return {
                    "status": f"Already {result['Duplicate_Api_Call']['response']}",
                    "message": "Duplicate Api Call"
                }
            if result.get('Duplicate_Lead', False):
                logger.info("Duplicate lead found")
                time_taken = (time.time() - start_time) * 1000
                logger.info(f"Submit request completed for data in {time_taken}ms")
                return {
                    "status": "REJECTED",
                    "code": "12_DUPLICATE",
                    "message": "This is a duplicate lead"
                }
            if "fetch_oem_data" in result:
                logger.info("OEM data found")
                fetched_oem_data = result['fetch_oem_data']
    if fetched_oem_data == {}:
        logger.info("OEM data is empty")
        time_taken = (time.time() - start_time) * 1000
        logger.info(f"Submit request completed for data in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    if 'threshold' not in fetched_oem_data:
        logger.info("Threshold not found in OEM data")
        time_taken = (time.time() - start_time) * 1000
        logger.info(f"Submit request completed for data in {time_taken}ms")
        return {
            "status": "REJECTED",
            "code": "20_OEM_DATA_NOT_FOUND",
            "message": "OEM data not found"
        }
    oem_threshold = float(fetched_oem_data['threshold'])

    # if dealer is not available then find nearest dealer
    logger.info("Looking for nearest dealer")
    if not dealer_available:
        lat, lon = get_customer_coordinate(obj['adf']['prospect']['customer']['contact']['address']['postalcode'])
        nearest_vendor = db_helper_session.fetch_nearest_dealer(oem=make,
                                                                lat=lat,
                                                                lon=lon)
        obj['adf']['prospect']['vendor'] = nearest_vendor
        dealer_available = True if nearest_vendor != {} else False

    # enrich the lead
    try:
        logger.info("Enriching lead data for ML input")
        start_time_enrich = time.time()
        model_input = get_enriched_lead_json(obj)
        enrich_time_taken = (time.time() - start_time_enrich) * 1000
        logger.info(f"Lead data enriched in {enrich_time_taken}ms")
    except Exception as e:
        logger.error(f"Error occurred while enriching lead data: {e.message}")

    # convert the enriched lead to ML input format
    try:
        logger.info("Converting the enriched data to ML input format")
        start_time_mlinput = time.time()
        ml_input = conversion_to_ml_input(model_input, make, dealer_available)
        mlinput_time_taken = (time.time() - start_time_mlinput) * 1000
        logger.info(f"Completed data conversion to ML input format in {mlinput_time_taken}ms")
    except Exception as e:
        logger.error(f"Error occurred while converting lead data to ML format: {e.message}")

    # score the lead
    try:
        logger.info("Scoring the lead data")
        start_time_scoring = time.time()
        result = score_ml_input(ml_input, make, dealer_available)
        scoring_time_taken = (time.time() - start_time_scoring) * 1000
        logger.info(f"Calculated score for lead data in {scoring_time_taken}ms")
    except Exception as e:
        logger.error(f"Error occurred while scoring the lead data: {e.message}")

    # create the response
    response_body = {}
    if result >= oem_threshold:
        response_body["status"] = "ACCEPTED"
        response_body["code"] = "0_ACCEPTED"
    else:
        logger.info("Score for lead data is less than OEM threshold")
        response_body["status"] = "REJECTED"
        response_body["code"] = "16_LOW_SCORE"

    # verify the customer
    if response_body['status'] == 'ACCEPTED':
        contact_verified = await new_verify_phone_and_email(email, phone)
        if not contact_verified:
            logger.info(f"Contact verification failed for email {email} phone {phone}")
            response_body['status'] = 'REJECTED'
            response_body['code'] = '17_FAILED_CONTACT_VALIDATION'

    lead_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, email + phone + last_name + make + model))
    logger.info(f"Generated lead uuid: {lead_uuid}")
    item, path = create_quicksight_data(obj['adf']['prospect'], lead_uuid, response_body['status'],
                                        response_body['code'], model_input)
    # insert the lead into ddb with oem & customer details
    # delegate inserts to sqs queue
    if response_body['status'] == 'ACCEPTED':
        logger.info(f"Response status: {response_body[status]}")
        logger.info(f"Creating model filter for {make}")
        try:
            model_filter_start = time.time()
            make_model_filter = db_helper_session.get_make_model_filter_status(make)
            model_filter_time_taken = (time.time() - model_filter_start) * 1000
            logger.info(f"Time taken to create model filter:{model_filter_time_taken}ms")
        except Exception as e:
            logger.error(f"Error occurred while creating model filter for lead {lead_uuid}: {e.message}")    
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
        logger.info("Inserting message into sqs queue")
        try:
            res = sqs_helper_session.send_message(message)
        except Exception as e:
            logger.error(f"Error occurred while inserting lead with uuid {lead_uuid} into sqs: {e.message}")

    else:
        
        logger.info(f"Response status: {response_body[status]}")
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
        logger.info("Inserting message into sqs queue")
        try:
            res = sqs_helper_session.send_message(message)
        except Exception as e:
            logger.error(f"Error occurred while inserting lead with uuid {lead_uuid} into sqs: {e.message}")

    time_taken = (int(time.time() * 1000.0) - start)
    logger.info(f"Submit request completed in {time_taken}ms")
    response_message = f"{result} Response Time : {time_taken} ms"

    return response_body
