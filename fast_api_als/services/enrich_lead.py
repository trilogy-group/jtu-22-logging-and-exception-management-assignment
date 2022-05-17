import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""
logger=logging.getlogger(__name__)
logger.setLevel(logging.DEBUG)

formatter=logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

file_handler=logging.FileHandler('enrich.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def get_enriched_lead_json(adf_json: dict) -> dict:
    try:
        pass
    except KeyError:
        logger.error("Keyerror exception occured")
        pass