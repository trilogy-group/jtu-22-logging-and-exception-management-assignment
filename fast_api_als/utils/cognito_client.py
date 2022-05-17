import logging
from fastapi import HTTPException

def get_user_role(token):

    if (int(token) == 0):
        return "Admin"
    else:
        logging.error('fn get user role: Invalid token')
        raise Exception('fn get user role: Invalid token')