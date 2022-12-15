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
    logging.info(f"S3 data created with {lead_uuid}")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))
    logging.info("Request body parsed")

    if 'lead_uuid' not in body or 'converted' not in body:
        logging.error("'lead_uuid' or 'converted' key missing in body.")
        # throw proper HTTPException
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'lead_uuid' or 'converted' missing")
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        logging.error(f"Permission denied to {role}")
        # throw proper HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only OEM users can request")

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        logging.info("Lead conversion updated")
        data, path = get_quicksight_data(lead_uuid, item)
        try:
            s3_helper_client.put_file(data, path)
        except Exception as e:
            logging.error("Failed to put file in S3"+ str(e))
            raise e
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        logging.error("Lead conversion update failed")
        # throw proper HTTPException
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
