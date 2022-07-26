import json
from fastapi import APIRouter, Depends
import logging
import time

from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from boto3.exception import S3UploadFailedError, RetriesExceededError

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
    logger.info("Quicksight data for lead_uuid " + str(lead_uuid) + "created successfully")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        logger.error('Lead UUID/converted missing from request')
        raise HTTPException('Lead UUID/converted missing from request')
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        # throw proper HTTPException
        raise HTTPException('Cannot execute request, Role is not OEM, UUID: ' lead_uuid)

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        try:
            s3_helper_client.put_file(data, path)
        except S3UploadFailedError as e:
            logger.error(e.message)
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": e.message
            }
        except RetriesExceededError as e:
            logger.error(e.message)
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": e.message
            }
        logger.info("S3 upload successful")
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        logger.error("Couldn't update lead conversion for lead_uuid={lead_uuid}, oem={oem}, converted={converted}")
        raise HTTPException("Couldn't update lead conversion")
