import time
import httpx
import asyncio
from fast_api_als.utils.logger import logger
from fast_api_als.constants import (
    ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
    ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
    ALS_DATA_TOOL_SERVICE_URL,
    ALS_DATA_TOOL_REQUEST_KEY)

"""
How can you write log to understand what's happening in the code?
You also trying to undderstand the execution time factor.
"""

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start_time = time.time() * 1000
    if value == '':

        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    time_taken = time.time() * 1000 - start_time
    logger.info(f"Validation completed for topic {topic} in {time_taken} ms")

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    logger.info(f"Validating Phone number {phone_number} and email {email}")
    start_time = time.time() * 1000
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
            logger.info(f"Validation successful for email {email}")
        else:
            logger.info(f"Validation failed for email {email}")
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
            logger.info(f"Validation successful for phone number {phone_number}")
        else:
            logger.info(f"Validation failed for phone number {phone_number}")
    time_taken = time.time() * 1000 - start_time
    logger.info(f"Validation Time for email {email} and phone number {phone_number} : {time_taken} ms")
    return email_valid | phone_valid
