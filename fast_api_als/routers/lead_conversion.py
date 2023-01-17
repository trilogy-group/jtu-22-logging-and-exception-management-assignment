import json
from fastapi import APIRouter, Depends
import logging
import time

from fastapi import Request, HTTPException
from starlette import status

router = APIRouter()

"""
write proper logging and exception handling
"""

logger = logging.getLogger(__name__) # To automatically know name of the current module

try:
    from fast_api_als.database.db_helper import db_helper_session
    from fast_api_als.quicksight.s3_helper import s3_helper_client
    from fast_api_als.services.authenticate import get_token
    from fast_api_als.utils.cognito_client import get_user_role
except:
    raise ImportError("Import Error in lead_conversion.py from fast_api_als")
    logger.error("Import Error in lead_conversion.py from fast_api_als")

def get_quicksight_data(lead_uuid, item):
    logger.info("Creation of lead converted data started in get_quicksight_data")
    if item is None:
        raise ValueError
        logger.error("get_quicksight_data called with NULL info")

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
    logger.info("Creation of Data for dumping into S3 successful")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    logger.info("Waiting for Request body")
    start = time.time()
    body = await file.body()
    end = time.time()
    elapsedTime = (end-start)*1000
    logger.info(f"Request body received in {elapsedTime} ms")
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        if 'lead_uuid' not in body:
            raise HTTPException(status_code=400, detail="Bad request. lead_uuid not found in body")
        
        if 'converted' not in body:
            raise HTTPException(status_code=400, detail="Bad request. converted not found in body")
        
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        # throw proper HTTPException
        logger.info(f"Bad Request: User role is not OEM. It is {role}.")
        raise HTTPException(status_code=401, detail=f"Bad Request: User role is not OEM. It is {role}.")
        
    logger.info("User is OEM. Starting the lead_conversion update")
    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logger.info(f"Lead Conversion successful. UUID = {lead_uuid}")
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        raise HTTPException(status_code=500, detail="Lead Conversion update Failed")
        logger.error("Lead Conversion update Failed")
        
