import calendar
import time
import logging
from fastapi import HTTPException
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants
from fast_api_als.utils.adf import check_validation
"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    # Check if adf json is valid
    validation_check = check_validation(adf_json)[0]

    # Throw exception if invalid
    if not validation_check:
        logging.error("Invalid adf_json")
        raise HTTPException(status_code=400, detail="Invalid adf_json")