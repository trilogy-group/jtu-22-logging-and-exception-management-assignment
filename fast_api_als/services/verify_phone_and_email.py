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

logger = logging.getLogger(__name__)

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    logger.info("call_validation_service started")
    start_time = time.time()
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    end = time.time()
    timeConsumed = (end-start)*1000
    logger.info(f"call_validation_service completed in {timeConsumed} ms.")
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    logger.info("verify_phone_and_email started")
    start_time = time.time()
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
            logger.info("Valid email in verify_phone_and_email.")
            email_valid = True
        else:
            logger.info("Invalid email in verify_phone_and_email.")
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            logger.info("Valid phone in verify_phone_and_email.")
            phone_valid = True
        else:
            logger.info("Invalid phone in verify_phone_and_email")

    
    end = time.time()
    timeConsumed = (end-start)*1000
    logger.info(f"verify_phone_and_email completed successfully in {timeConsumed} ms.")
    return email_valid | phone_valid
