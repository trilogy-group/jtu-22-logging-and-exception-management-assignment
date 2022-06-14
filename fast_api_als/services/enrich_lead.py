import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""

logging.basicConfig(level=logging.INFO,format='%(levelname)s:%(asctime)s:%(module)s')

def get_enriched_lead_json(adf_json: dict) -> dict:
    # Checking data-type
    valid=isinstance(dict, adf_json)

    if not valid:
        logging.error("Invalid datatype dictionary file")
        raise TypeError()

    logging.info("Enriched lead json.")
    dic=dict()
    return dic