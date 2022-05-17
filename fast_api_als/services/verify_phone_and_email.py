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

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start = int(time.time() * 1000.0)
    if value == '':
        logging.info("Email or Phone Value Empty")
        return

    logging.info("Getting Response")
    t_time = int(time.time() * 1000.0)
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)
    t_time_taken = int(time.time() * 1000.0) - t_time
    logging.info(f"Response fetched in {t_time_taken}ms")

    r = response.json()
    data[topic] = r
    time_taken = int(time.time() * 1000.0) - start
    logging.info(f"Validated {topic} in {time_taken}ms")
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    start = int(time.time() * 1000.0)
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
    
    try:
        logging.info("Gathering phone and email validation responses")
        await asyncio.gather(
            call_validation_service(email_validation_url, "email", email, data),
            call_validation_service(phone_validation_url, "phone", phone_number, data),
        )
        logging.info("Gathered Responses")
        if "email" in data:
            if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
                email_valid = True
        if "phone" in data:
            if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
                phone_valid = True
        logging.info("Checked Phone and Email Validation")
    except as e:
        logging.error(f"Phone and email verification failed: {e.message}")
    time_taken = int(time.time() * 1000.0) - start
    logging.info(f"Phone number {phone_number} and email {email} verified in {time_taken}ms")
    return email_valid | phone_valid
