import logging
from fastapi import APIRouter
logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s')


router = APIRouter()
#dummy router
@router.get("/user")   
async def get_user_details(user_id):
    '''
    This Function returns user details
    '''
    logging.info("Got user details")
    return {"message": "User details"}