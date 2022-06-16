import time
import httpx
import asyncio
import logging
from fast_api_als.constants import (
    ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
    ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
    ALS_DATA_TOOL_SERVICE_URL,
    ALS_DATA_TOOL_REQUEST_KEY)

"""
How can you write log to understand what's happening in the code?
You also trying to undderstand the execution time factor.
"""

logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(asctime)s:%(module)s')

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2

    t1=time.process_time()
    if value == '':
        logging.warning("Invalid service , " + topic + "not added in data dictionary")
        return
    logging.info("Fetching ")
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    t2=time.process_time()
    time_factor=(t2-t1)*1000

    logging.info("Validation request resolved in " + str(time_factor) + "ms time")

    r = response.json()
    data[topic] = r
    logging.info("Valid Services , " + topic + "Added in data dictionary")
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    email_validation_url = '{}?Method={}&RequestKey={}&EmailAddress={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        email)
    phone_validation_url = '{}?Method={}&RequestKey={}&PhoneNumber={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        phone_number)
    email_valid = False
    phone_valid = False
    data = {}

    t1=time.process_time()

    await asyncio.gather(
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            email_valid = True
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
    
    if not (email_valid or phone_valid):
        logging.info("Invalid phone number and email and Response was not added")
    else:
        logging.info("Validity check successful and Response added")

    t2=time.process_time()

    time_factor=(t2-t1)*1000

    logging.info("Time taken for validation =" + str(time_factor) + "ms")

    return email_valid | phone_valid
