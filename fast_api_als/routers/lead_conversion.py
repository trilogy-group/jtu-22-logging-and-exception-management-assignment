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
    # the data object "item" must have 'make' and 'model' keys, if not throw an exception

    if "make" not in item:
        logging.error("fn get_quicksight_data : 'make' key is not present in item")
        raise Exception("fn get_quicksight_data : 'make' key is not present in item")

    if "model" not in item:
        logging.error("fn get_quicksight_data : 'model' key is not present in item")
        raise Exception("fn get_quicksight_data : 'model' key is not present in item")


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
    start = time.process_time()
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        logging.error("/conversion : 'lead_uuid' key or 'converted' key is not present in body")
        raise HTTPException(status_code = 500, detail="conversion: fn submit : 'lead_uuid' key or 'converted' key is not present in body")
        
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        # throw proper HTTPException
        logging.error("/conversion: Unauthorized access(role != `OEM`)")
        raise HTTPException(status_code = 401, detail="conversion: fn submit  : Unauthorized access(role != `OEM`)")
        
    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        time_taken = (time.process_time() - start) * 1000

        logging.info(f"/conversion: The response time {time_taken} ms")
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        logging.error("/conversion: Unable to update lead conversion")
        raise HTTPException(status_code = 500, detail="conversion: fn submit: Unable to update lead conversion")
