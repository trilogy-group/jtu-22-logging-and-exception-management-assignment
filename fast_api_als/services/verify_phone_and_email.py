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

log = logging.getLogger(__name__)

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        try:
            response = await client.get(url)
            log.info(f'Request successful to client URL {url}')
        except httpx.RequestError as re:
            log.error(f'Error occured while requesting {re.request.url}')
        except Exception as e:
            log.error(f'Error occured while requesting URL due to {e}')
            

    r = response.json()
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
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

    start = int(time.time()*1000)
    await asyncio.gather(
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    end = int(time.time()*1000)
    time_taken = end - start
    log.info(f'[{time_taken}] Validation done successfully.')
    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            email_valid = True
            log.info(f'User verified by email: {email}')
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
            log.info(f'User verified by phone number: {phone_number}')
    return email_valid | phone_valid
