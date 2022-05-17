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
    try:
        pass
    except KeyError:
        logging.exception(f"[Enrich Lead] Key not found in ADF JSON.{adf_json}")
        return {}
    except:
        logging.exception(f"[Enrich Lead] Some exception occured while enriching lead. {adf_json}")
        return {}