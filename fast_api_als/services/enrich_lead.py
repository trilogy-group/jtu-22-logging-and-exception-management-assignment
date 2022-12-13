import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

log = logging.getLogger(__name__)

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    if not isinstance(adf_json, dict) :
        #not a dict
        log.info('adf_json is not a dict')
        raise TypeError
    if adf_json is None or adf_json=={}:
        #empty dict
        log.info("adf_json is null or empty")
        raise ValueError
    if 'adf' not in adf_json:
        #field not found
        log.info("adf field is not found in adf_json object")
        raise KeyError
    
    log.info("Valid adf_json is passed as argument to get_enriched_lead_json")
    pass