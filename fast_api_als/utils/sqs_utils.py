import logging
from fastapi import HTTPException


def sqs_helper_session():
    logging.info('fn sqs_helper_session: Called')