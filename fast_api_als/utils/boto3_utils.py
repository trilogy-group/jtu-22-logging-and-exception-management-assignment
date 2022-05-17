import logging

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')

def get_user_details():
    '''
    This Dummy Function returns boto3 session
    '''
    logging.info("boto3 session is created")
    return "boto3 session"