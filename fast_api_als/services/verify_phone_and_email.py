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
    start = (int)(time.time()*1000)
    logging.info(f'{topic} validation service started.')
    if value == '':
        logging.warning("value is empty")
        end = (int)(time.time()*1000)
        logging.info(f'{topic} validation service ended in {end-start} ms.')
        return
    async with httpx.AsyncClient() as client:  # 3
        logging.info("Recieving client data.")
        t1 = (int)(time.time()*1000)
        response = await client.get(url)
        t2 = (int)(time.time()*1000)
        logging.info(f'Recieved client data in {t2-t1} ms.')
    
    r = response.json()
    data[topic] = r
    end = (int)(time.time()*1000)
    logging.info(f'{topic} validation service ended in {end-start} ms.')
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    logging.info("Veryfing phone and email")
    t1 = (int)(time.time()*1000)
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
        # logging already done in call_validation_service function
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            email_valid = True
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
    t2 = (int)(time.time()*1000)
    logging.info(f'Phone and email verification complete in {t2-t1} ms.')
    return email_valid | phone_valid
