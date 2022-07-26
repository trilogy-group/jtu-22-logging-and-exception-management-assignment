import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

"""
what exceptions can be thrown here?
"""
logging.basicConfig(filename="applicationLogs.txt", filemode='w',level=logging.DEBUG,  format = '%(asctime)s %(levelname)s: %(message)s',)

def get_enriched_lead_json(adf_json: dict) -> dict:
    try:
        return 1
    except KeyError as e:
        logging.error("Key error, key not found in dictionary, error:", e)
        return None
    except Exception as e:
        logging.error("Error while getting enriched lead json, error:", e)
        return None
