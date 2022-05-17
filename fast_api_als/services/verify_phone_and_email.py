import time
import httpx
import asyncio
from fast_api_als.utils.base_logger import logger
from fast_api_als.constants import (
    ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
    ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
    ALS_DATA_TOOL_SERVICE_URL,
    ALS_DATA_TOOL_REQUEST_KEY)


async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    start_time = time.time()
    if value == '':
        return
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    data[topic] = r
    time_taken = int((time.time() - start_time) * 1000)
    logger.info(f"Validated {topic} - {value} in {time_taken}ms")


async def verify_phone_and_email(email: str, phone_number: str) -> bool:
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
            email_valid = True
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            phone_valid = True
    time_taken = int((time.time() - start_time) * 1000)
    logger.info(f"Phone {phone_number} verified = {phone_valid}, email {email} verified = {email_valid} in {time_taken}ms")
    return email_valid | phone_valid
