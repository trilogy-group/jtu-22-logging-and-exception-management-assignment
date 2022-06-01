import calendar
import time
from dateutil import parser
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.utils.logger import logger
from fast_api_als import constants
from fast_api_als.utils import validate_adf_values

"""
what exceptions can be thrown here?
"""

def get_enriched_lead_json(adf_json: dict) -> dict:
    
    if not adf_json.has_key('adf'):
        logger.error("adf missing in lead json sent for enrichment")
        raise KeyError("adf is missing from adf_json passed for enrichment")
    
    res = validate_adf_values(adf_json)
    if res['status'] == 'Rejected':
        logger.error(f"adf passed for enriching is invalid: {res['message']}")
        raise ValueError("adf_json passed for enrichment is missing some values")
    
    logger.info("adf_json passed for enrichment is valid")
