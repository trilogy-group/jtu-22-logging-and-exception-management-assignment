import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""

# In the function get_enriched_lead_json, if given adf_json is not valid : throw an error
# If valid, check if adf_json have all the required fields or attributes

def get_enriched_lead_json(adf_json: dict) -> dict:
    pass