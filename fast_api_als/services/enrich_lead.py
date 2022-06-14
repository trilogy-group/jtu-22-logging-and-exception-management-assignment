import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    if type(adf_json) is not dict:
        logging.error("argument of get_enriched_lead_json must be of type dict")
        raise TypeError("argument of get_enriched_lead_json must be of type dict")
    
    enriched_lead = {}

    try:
        enriched_lead['attribute'] = adf_json['attr']
    except:
        logging.error("argument of get_enriched_lead_json must have key 'attr'")
        raise Exception("argument of get_enriched_lead_json must have key 'attr'")
    
    logging.info(f"returned enriched lead: {enriched_lead}")
    return enriched_lead