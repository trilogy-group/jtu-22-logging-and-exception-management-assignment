import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""
logger = logging.getLogger(__name__)

def get_enriched_lead_json(adf_json: dict) -> dict:
    if adf_json is None or adf_json == {}:
        raise ValueError
    else:
        logger.info('Valid adf_json object passed to get_enriched_lead_json')