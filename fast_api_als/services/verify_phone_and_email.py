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
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        try:
            response = await client.get(url)
        except httpx.RequestError as re:
            logger.error(f'Error occurred while requesting {re.request.url}')
        except Exception as e:
            logger.error(f'Get request failed for url: {url} due to {e}')

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

    logger.debug(f'Email validation URL: {email_validation_url}')
    logger.debug(f'Phone validation URL: {phone_validation_url}')


    logger.debug('Validation service called')
    start_time = int(time.time() * 1000.0)
    await asyncio.gather(
        call_validation_service(email_validation_url, "email", email, data),
        call_validation_service(phone_validation_url, "phone", phone_number, data),
    )
    end_time = int(time.time() * 1000.0)
    logger.info(f'Total time taken by validation service: {end_time - start_time}ms')

    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            email_valid = True
            logger.info(f'User verified by email: {email}')

    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
            logger.info(f'User verified by phone: {phone_number}')

    if not (email_valid or phone_valid):
        logger.info(f'User could not be verified by email or phone')

    return email_valid | phone_valid
