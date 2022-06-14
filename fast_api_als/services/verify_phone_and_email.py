import time
import httpx
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from fast_api_als.constants import (
    ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
    ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
    ALS_DATA_TOOL_SERVICE_URL,
    ALS_DATA_TOOL_REQUEST_KEY)

"""
How can you write log to understand what's happening in the code?
You also trying to understand the execution time factor.
"""

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start_time = time.process()
    if value == '':
        logging.debug(topic + " doesn't contain any value in the call_validation_service call" )
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)
    time_taken = (time.process() - start_time ) * 1000

    logging.info("The time taken to resolve the Validation request through API is : " + str(time_taken))

    r = response.json()
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    start_time = time.process()
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
    time_taken = (time.process() - start_time ) * 1000
    if not (email_valid or phone_valid):
        logging.info("The phone number and email are not valid and time taken is " + str(time_taken))
    else :
        logging.info("The validation of phone number or email was successful and time taken is " + str(time_taken))
    
    return email_valid | phone_valid
