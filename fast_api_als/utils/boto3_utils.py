import logging

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')

def get_boto3_session():
    '''
    This Dummy Function returns boto3 session
    '''
    logging.info("boto3 session is created")
    return "boto3 session"