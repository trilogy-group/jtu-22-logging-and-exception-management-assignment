import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants
logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    '''
    1.type error
    2.key error
    '''
    if not isinstance(adf_json, dict):
        raise TypeError

    #and raise KeyError     for key not present
    d = dict()
    try:
        d['something']= adf_json['something']   #something is not present in adf_json
    except:
        raise KeyError()
    logging.info("Got enriched lead json.")
    return d