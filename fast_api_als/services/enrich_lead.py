import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

logger = logging.getLogger(__name__) # To automatically know name of the current module

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    if adf_json is None:
        logger.error("adf_json is null")
        raise ValueError("adf_json is null")
    if adf_json=={}:
        logger.error("adf_json is empty")
        raise ValueError("adf_json is empty")
    if(type(adf_json) is not dict):
        logger.error("adf_json is not a dictionary object")
        raise TypeError("adf_json is not a dictionary object")
    logger.info("adf_json passed the get_enriched_lead_json check")
    pass