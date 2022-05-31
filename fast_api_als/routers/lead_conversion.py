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

"""
write proper logging and exception handling
"""

logger = logging.getLogger(__name__)

def get_quicksight_data(lead_uuid, item):
    """
            Creates the lead converted data for dumping into S3.
            Args:
                lead_uuid: Lead UUID
                item: Accepted lead info pulled from DDB
            Returns:
                S3 data
    """
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
    try:
        body = await file.body()
        body = json.loads(str(body, 'utf-8'))
        logger.info('Body of request parsed successfully')
    except json.JSONDecodeError as jde:
        logger.error(f'Decoding of JSON failed as passed file is not a valid JSON document: {jde}')
    except Exception as e:
        logger.error(f'Failed to load file body due to {e}')


    if 'lead_uuid' not in body or 'converted' not in body:
        if 'lead_uuid' not in body:
            raise HTTPException(status_code=400, detail="lead_uuid field not found in body")
        else:
            raise HTTPException(status_code=400, detail="converted field not found in body")

        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        logger.error(f'Attempt to call submit by user having token: {token} failed as user does not have role OEM')
        raise HTTPException(status_code=401, detail="User with role not OEM is not authorised to submit")

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logger.info(f'File submitted by lead_uuid: {lead_uuid}')
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        logger.error(f'Attempt to call submit by user having token: {token}, lead_uuid: {lead_uuid} and item: {item} failed due to failed lead conversion')
        raise HTTPException(status_code=500, detail='Lead Conversion failed')
