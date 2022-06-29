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
# Creating logger file and configuring
logging.basicConfig(filename="newFile.log", format='%(asctime)s %(message)s', filemode='w')

# Creating object logger
logger = logging.getLogger()

# Setting threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start_time = int(time.process_time()*1000.0)

    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    end_time = int(time.process_time()*1000.0)
    logger.info(f"verify_phone_and_email: call_validation_service: Took {end_time-start_time}ms to execute the function")
    logger.info("verify_phone_and_email: call_validation_service: Function executed successfully")
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    #Start time
    start_time = int(time.process_time()*1000.0)

    email_validation_url = '{}?Method={}&RequestKey={}&EmailAddress={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        email)
    logger.info("verify_phone_and_email: verify_phone_and_email: Generated email validation url")
    phone_validation_url = '{}?Method={}&RequestKey={}&PhoneNumber={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        phone_number)
    logger.info("verify_phone_and_email: verify_phone_and_email: Generated phone validation url")
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
    end_time = int(time.process_time()*1000.0)
    logger.info(f"verify_phone_and_email: verify_phone_and_email: Function executed in {end_time-start_time}ms to run")
    return email_valid | phone_valid
