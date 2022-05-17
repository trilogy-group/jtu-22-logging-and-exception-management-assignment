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
logger=logging.getlogger(__name__)
logger.setLevel(logging.DEBUG)

formatter=logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

file_handler=logging.FileHandler('verify.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

logger.info("call_validation service initiated")
async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
logger.info("call validation service completed")
    
logger.info("verify_phone_and_email initiated")
async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    start=int(time.time()*1000.0)
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
    end=int(time.time()*1000.0)
    logger.info("verify_phone_and_email completed")
    logger.info("Execution time is:{end-start}")
    return email_valid | phone_valid
