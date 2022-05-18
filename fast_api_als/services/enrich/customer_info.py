import random
from logger import logger


def get_contact_details(obj):
    '''[Dummy function]'''
    logger.info('get contact details')

    if random.randrange(2) == 0:
        raise Exception('Invalid obj')
    else:
        return '1'
