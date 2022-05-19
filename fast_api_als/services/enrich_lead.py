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

    # assuming returned object to be a
    a = {
        'assuming' : 'a',
        'is' : 'returned'
    }

    try : 
        assert (type(a) is dict)
        return a
    except exception as e : 
        logging.error('Object which is returned not of type dict' , exc_info = True)
    pass