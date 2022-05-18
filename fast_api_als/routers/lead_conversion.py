import json
from fastapi import APIRouter, Depends, HTTPException
from logger import logger
import time

from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role

router = APIRouter()

"""
write proper logger and exception handling
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

    if 'make' not in item:
        logger.error(
            'property `make` missing in item')
        raise Exception('property `make` missing in item')

    if 'model' not in item:
        logger.error(
            'property `model` missing in item')
        raise Exception('property `model` missing in item')

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

    start = int(time.time() * 1000.0)
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        logger.error(
            "[Lead Conversion]: `lead_uuid` or `converted` missing in body")
        raise HTTPException(
            status_code=500, detail="`lead_uuid` or `converted` missing in body")

    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        logger.error(
            "[Lead Conversion]: Unauthorized Role")
        raise HTTPException(
            status_code=401, detail="Unauthorized Role")

    is_updated, item = db_helper_session.update_lead_conversion(
        lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        now = int(time.time() * 1000.0)
        logger.info(f'Completed in {now - start}ms')

        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        now = int(time.time() * 1000.0)
        logger.error(
            f"[Lead Conversion]: Unable to update lead conversation, time taken: {now - start}ms")
        raise HTTPException(
            status_code=500, detail="Unable to update lead conversation")
