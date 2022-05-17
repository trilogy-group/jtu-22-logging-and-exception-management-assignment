import time
import httpx
import asyncio
import logging
from fast_api_als.constants import (
    ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
    ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
    ALS_DATA_TOOL_SERVICE_URL,
    ALS_DATA_TOOL_REQUEST_KEY)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s-%(asctime)s: %(message)s")
filehandler = logging.FileHandler('db.log')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)
"""
How can you write log to understand what's happening in the code?
You also trying to undderstand the execution time factor.
"""

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    logging.info(f'call validation service called for {topic}')
    if value == '':
        logging.info('value is empty for call validation')
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    logging.info(f'topic field of data filled with {r}')
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    t1 = [int(time.time() * 1000.0)]
    logging.info(f'verifying phone {phone_number} and email {email}')
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
    logging.info(f'email verified: {email_valid}')
    logging.info(f'phone number verified: {phone_valid}')
    t2 = [int(time.time() * 1000.0)]
    logging.info(f'time taken for verify_phone_and_email: {t2-t1}')
    return email_valid | phone_valid
