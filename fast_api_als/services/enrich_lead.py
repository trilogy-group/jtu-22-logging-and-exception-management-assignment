import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

logging.basicConfig(level=logging.INFO , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    # Check the type of adf_json if it a dictionary or not , if is not a dictionary the throw an exception
    if not (isinstance(adf_json, dict)) :
        logging.error("The datatype of adf_json received is not a dictionary")
        raise TypeError
    
    logging.info("Received a adf_json dictionary successfully")

    dictionary = dict()
    # do something using dictionary and adf_json 

    return dictionary
    