import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""
# Creating logger file and configuring
logging.basicConfig(filename="newFile.log", format='%(asctime)s %(message)s', filemode='w')

# Creating object logger
logger = logging.getLogger()

# Setting threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


def get_enriched_lead_json(adf_json: dict) -> dict:
    pass

    # Checking if the adf_json dictionary is empty
    bool_empty= not bool(adf_json)

    if(boolempty):
        logger.info("enrich_lead: get_enriched_lead_json: adf_json is empty")
        return Exception("Dictionary is empty")
    logger.info("enrich_lead: get_enriched_lead: Function ran successfully")
    return adj_json