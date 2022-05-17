import logging
logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')

#dummy function
def get_user_details(user_id):
    '''
    This Function returns user details
    '''
    logging.info("Got user details")
    return {"message": "User details"}