from asyncio.log import logger
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
    logging.info("Calling validation service to verify {0}".format(value))
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    verification_start_time=time.time()
    logging.info("Function for verifying phone and email, executing")
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
            logging.info("Email: {0} verified".format(data["email"]))
            email_valid = True
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True

    logging.info("Total time for verifying phone or email: {0}ms".format((time.time()-verification_start_time)*1000))
    return email_valid | phone_valid
