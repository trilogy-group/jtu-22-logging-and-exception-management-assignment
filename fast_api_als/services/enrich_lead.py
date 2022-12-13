import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als import constants

def get_enriched_lead_json(adf_json: dict) -> dict:
    if not isinstance(adf_json, list):
        raise TypeError(f"Expected {dict}, got {type(x)}")
    return adf_json