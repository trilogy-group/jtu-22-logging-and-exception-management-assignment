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
    dict_keys = adf_json.keys()
    if("adf" not in dict_keys):
        logging.error("adf key missing")
        raise KeyError
    try: 
        temp = json.loads(adf_json) 
        #do some work
    except ValueError as e:
        logging.error("Value error "+str(e))
        raise ValueError 
        