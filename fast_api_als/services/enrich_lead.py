import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

"""
what exceptions can be thrown here?
"""

def get_enriched_lead_json(adf_json: dict) -> dict:
    try:
        make = obj['adf']['prospect']['vehicle']['make']
        model = obj['adf']['prospect']['vehicle']['model']
    except Exception as e:
        logging.error(f"Lead data is incomplete: {e.message}")
        return adf_json