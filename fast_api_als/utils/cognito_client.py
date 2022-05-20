import logging

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')

def get_user_role():
    '''
    This Dummy Function returns users role
    '''
    logging.info("fetched user role.")
    return "user role"