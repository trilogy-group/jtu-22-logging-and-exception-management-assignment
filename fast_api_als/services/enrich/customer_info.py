import random
import logging


def get_contact_details(obj):
    '''[Dummy function]'''
    logging.info('get contact details')

    if random.randrange(2) == 0:
        raise Exception('Invalid obj')
    else:
        return '1'
