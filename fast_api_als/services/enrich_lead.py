import calendar
import time
from typing import Type
from logger import logger
from dateutil import parser
from database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:

    # Check if adf_json is valid and throw an error if not
    if not isinstance(adf_json, dict):
        logger.error(
            '[Get Enriched Lead JSON] Invalid adf json type')
        raise TypeError

    # Check if adf_json has all the required properties
    # Assuming adf_json must have a key named 'required'
    if 'required' not in adf_json:
        logger.error(
            '[Get Enriched Lead JSON] key `required` missing from adf json')
        raise KeyError
