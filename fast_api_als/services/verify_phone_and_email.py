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
    if value == '':
        logging.info("Found empty value")
        return
    logging.info("Waiting for response from client")
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)
    logging.info("Got response from client")
    logging.debug("The following response was received"+response)

    r = response.json()
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    email_validation_url = '{}?Method={}&RequestKey={}&EmailAddress={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        email)
    logging.debug("Email validation url "+email_validation_url)
    phone_validation_url = '{}?Method={}&RequestKey={}&PhoneNumber={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        phone_number)
    logging.debug("Phone number validation url "+phone_validation_url)
    email_valid = False
    phone_valid = False
    data = {}

    await asyncio.gather(
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    logging.info("Verifying email and phone")
    logging.debug("Following data was received "+data)
    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            logging.info("Email valid")
            email_valid = True
        else:
            logging.error("Email invalid")
            raise ValueError
    else:
        logging.error("Email field not found in response")
        raise KeyError
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            logging.info("Phone number valid")
            phone_valid = True
        else:
            logging.error("Phone number invalid")
            raise ValueError
    else:
        logging.error("Phone field not found in response")
        raise KeyError
    return email_valid | phone_valid
