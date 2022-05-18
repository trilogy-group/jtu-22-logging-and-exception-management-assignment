import json
from fastapi import APIRouter, Depends
import logging
import time
from fastapi import HTTPException
from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s: %(message)s")
filehandler = logging.FileHandler('db.log')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)

router = APIRouter()

"""
write proper logging and exception handling
"""



def get_quicksight_data(lead_uuid, item):
    """
            Creates the lead converted data for dumping into S3.
            Args:
                lead_uuid: Lead UUID
                item: Accepted lead info pulled from DDB
            Returns:
                S3 data
    """
    logger.info(f'get_quicksight_data called with lead id {lead_uuid} and item {item}')
    data = {
        "lead_hash": lead_uuid,
        "epoch_timestamp": int(time.time()),
        "make": item['make'],
        "model": item['model'],
        "conversion": 1,
        "postalcode": item.get('postalcode', 'unknown'),
        "dealer": item.get('dealer', 'unknown'),
        "3pl": item.get('3pl', 'unknown'),
        "oem_responded": 1
    }

    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    logger.info('post request recieved at /conversion')
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        # HTTP 400 code exception: BadRequest 
        raise HTTPException(status_code=400, detail='bad request, body has invalid parameters')       

    lead_uuid = body['lead_uuid']
    converted = body['converted']
    logger.info(f'body has: lead_uuid {lead_uuid} and converted {converted}')
    oem, role = get_user_role(token)
    if role != "OEM":
        # throw proper HTTPException
        # HTTP 401 code exception: UnauthorizedException
        raise HTTPException(status_code=401, detail='Unauthorized access, role is not OEM') 
    
    logger.info(f'user role: {role}')
    is_updated, item = db_helper_session.update_lead_conversion(
        lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logger.info(f'post request accepted for /conversion')
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        # 404
        raise HTTPException(status_code=404, detail='data not found for lead conversion status update') 

