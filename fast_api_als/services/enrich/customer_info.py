import logging
from fastapi import HTTPException

def get_contact_details(obj):
    logging.info("get_contact_details: called")
    return "detail"

