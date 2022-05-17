import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""
logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

def get_enriched_lead_json(adf_json: dict) -> dict:
    # pass
    if isinstance(element, dict)
        logging.info("Adf Json is not of type dict")
        raise TypeError

    try:
        key = adf_json['key']
    except Exception as e:
        logging.error("Get Enriched Lead failed: {e.message}")