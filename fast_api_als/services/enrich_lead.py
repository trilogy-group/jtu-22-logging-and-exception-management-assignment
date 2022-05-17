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
    try:
        pass
    except KeyError:
        logging.error('KeyError exception occured, key not valid while accessing dictionary')