import json
from fastapi import APIRouter, Depends, HTTPException
import logging
import time

from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)s-%(message)s')

file_handler = logging.FileHandler('logs.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


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
    for id in item:
        if item[id] == '':
            logging.warning(f'{id} field empty in item')
            raise Exception(f'{id} field empty in item')
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
    logger.info('Lead converted data created for dumping into S3')
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        logger.error('lead_uuid or converted not in body')
        raise HTTPException(status_code=400, detail="lead_uuid or converted not in body")
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        logger.error("Unauthorized Role: User role not OEM")
        raise HTTPException(status_code=403, detail="Role of the user is not OEM")

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        logger.error('Lead conversion Failed')
        raise HTTPException(status_code=401, detail="Lead conversion Failed")
