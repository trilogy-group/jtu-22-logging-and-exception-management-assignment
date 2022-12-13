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

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start_time = int(time.process_time()*1000.0)
    if value == '':
        logging.info("%s missing", topic)
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    
    end_time = int(time.process_time()*1000.0)
    logging.info(f"verify_phone_and_email: call_validation_service: Took {end_time-start_time}ms to execute the function")

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    start_time = int(time.process_time()*1000.0)
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

    logging.info("Calling validation service for email and phone")
    await asyncio.gather(
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    logging.info("Call to validation service completed for email and phone")
    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            email_valid = True
            logging.info("Email valid")
        else: logging.info("Email invalid")
    else: logging.info("Email not validated")
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
            logging.info("Phone valid")
        else: logging.info("Phone invalid")
    else: logging.info("Phone not validated")
    end_time = int(time.process_time()*1000.0)
    logging.info(f"verify_phone_and_email: verify_phone_and_email: Function executed in {end_time-start_time}ms to run")
    return email_valid | phone_valid
