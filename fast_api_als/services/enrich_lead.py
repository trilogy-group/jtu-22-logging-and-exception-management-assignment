import calendar
import time
import logging
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session

from fast_api_als import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")

filehandler = logging.FileHandler('services.log')
filehandler.setFormatter(formatter)

logger.addHandler(filehandler)


"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    try:
        pass
    except KeyError:
        logger.error(f"Key coulnd't be found in the dictionary {adf_json}")