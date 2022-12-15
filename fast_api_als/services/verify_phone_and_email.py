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

# creating a logger
logger = logging.getLogger(__name__)

async def call_validation_service(url: str, topic: str, value: str, data: dict) -> None:  # 2
    if value == '':
        logger.info("Value was empty.")
        return
    logger.info("Calling validation service")
    async with httpx.AsyncClient() as client:  # 3
        response = await client.get(url)

    r = response.json()
    logger.debug("Updating the topic in data to json response")
    data[topic] = r
    

async def verify_phone_and_email(email: str, phone_number: str) -> bool:
    email_validation_url = '{}?Method={}&RequestKey={}&EmailAddress={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_EMAIL_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        email)
    
    logger.debug("Email validation url generated.")
    
    phone_validation_url = '{}?Method={}&RequestKey={}&PhoneNumber={}&OutputFormat=json'.format(
        ALS_DATA_TOOL_SERVICE_URL,
        ALS_DATA_TOOL_PHONE_VERIFY_METHOD,
        ALS_DATA_TOOL_REQUEST_KEY,
        phone_number)
    
    logger.debug("Phone validation url generated.")
    
    email_valid = False
    phone_valid = False
    data = {}

    await asyncio.gather(
        logger.info("Calling email validation service.")
        try:
            call_validation_service(email_validation_url, "email", email, data),
        except Exception as e:
            logger.error("Error in calling email_validation_service.")
            logger.info(e)
        
        logger.info("Email validation service called.")
        logger.info("Calling phone number validation service.")
        try:       
            call_validation_service(phone_validation_url, "phone", phone_number, data),
        except Exception as e:
            logger.error("Error in calling call_validation_service.")
            logger.info(e)
        
        logger.info("Phone validation service called.")
    )

    if "email" in data:
        if data["email"]["DtResponse"]["Result"][0]["StatusCode"] in ("0", "1"):
            logger.info("Email validated")
            email_valid = True
    if "phone" in data:
        if data["phone"]["DtResponse"]["Result"][0]["IsValid"] == "True":
            logger.info("Phone number validated")
            phone_valid = True
    
    logger.debug("Returning the response : whether email is valid or phone number is valid")
    return email_valid | phone_valid
