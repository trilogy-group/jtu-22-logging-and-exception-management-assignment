import logging

logging.basicConfig(
    level = logging.INFO,
    format = "{asctime} {levelname:<8} {message}",
    style= '{',
    filename = 'fast_api_als.log',
    filemode = 'a'
)

try:
    import calendar
    import time
    from dateutil import parser
    from fast_api_als.database.db_helper import db_helper_session
    from fast_api_als import constants
except ImportError as e:
    logging.error("Import Exception occurred!", exc_info = True)

"""
what exceptions can be thrown here?
"""


def get_enriched_lead_json(adf_json: dict) -> dict:
    if(type(adf_json) is not dict):
        logging.error("The passed object is not a dictionary!")
        raise ValueError("The passed object is not a dictionary!")
    pass