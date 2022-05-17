import calendar
import time
import logging
from dateutil import parser
from database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:

    # Check if adf_json is valid and throw an error if not
    # Check if adf_json has all the required properties 
    pass
