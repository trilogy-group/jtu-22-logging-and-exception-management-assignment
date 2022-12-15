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
    try:
        # process the dict 
        

    except KeyError as ke:
        logger.error("Key not found in adf_json", ke)
    except ValueError as ve:
        logger.error("Key can't take this value", ve)
        

        