import calendar
from http.client import HTTPException
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""

# Creating and configuring logger
logging.basicConfig(filename="newFile.log",
                    format='%(asctime)s %(message)s', filemode='w')

# Creating an object logger
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


def get_enriched_lead_json(adf_json: dict) -> dict:
    pass
    # checking for empty dictionary
    res = not bool(adf_json)
    if(res):
        return Exception("Dictionary is empty")

    # Exception handling for any attribute
    try:
        adf_json['someAttribute']
    except:
        raise Exception("someAttribute is not present in the dictionary")
    logger.info("enrich_lead:get_enriched_lead_json:Function ran successfully")
