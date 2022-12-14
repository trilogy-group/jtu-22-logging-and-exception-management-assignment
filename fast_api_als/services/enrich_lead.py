import calendar
import time
import json
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    if 'adf' not in adf_json.keys():
        raise KeyError
    try:
        json.loads(adf_json)
    except ValueError:
        raise ValueError
    pass