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

router = APIRouter()

"""
write proper logging and exception handling
"""

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

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
        start = int(time.time() * 1000.0)
        logging.info("Lead Conversion Request")
        body = await file.body()
        body = json.loads(str(body, 'utf-8'))

        logging.info("Checking required parameters in body")
        if 'lead_uuid' not in body or 'converted' not in body:
            # throw proper HTTPException
            logging.info("Parameters Missing: Conversion Request Terminated")
            raise HTTPException(status_code=400, detail="Required Parameters Missing")
            # pass
            
        lead_uuid = body['lead_uuid']
        converted = body['converted']

        logging.info("Checking Required permissions")
        oem, role = get_user_role(token)
        if role != "OEM":
            # throw proper HTTPException
            time_taken = int(time.time() * 1000.0) - start
            logging.info(f"Permissions Missing: Conversion Request Terminated in {time_taken}ms")
            raise HTTPException(status_code=403, detail="You do not have required permission")
            # pass

        logging.info("Updating Conversion Lead")
        is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
        if is_updated:
            logging.info("Getting QuickSight Data")
            data, path = get_quicksight_data(lead_uuid, item)
            logging.info("Uploading Conversion data on S3")
            s3_helper_client.put_file(data, path)
            time_taken = int(time.time() * 1000.0) - start
            logging.info(f"Conversion Lead with lead uuid {lead_uuid} Updation Successful in {time_taken}ms")
            return {
                "status_code": status.HTTP_200_OK,
                "message": "Lead Conversion Status Update"
            }
        else:
            # throw proper HTTPException
            time_taken = int(time.time() * 1000.0) - start
            logging.info(f"Conversion Lead with lead uuid {lead_uuid} Already Updated : Conversion Request Terminated in {time_taken}ms")
            raise HTTPException(status_code=400, detail="Conversion Lead was already updated")
            # pass
    except as e:
        logging.error(f"Conversion Request Failed: {e.message}")
        raise HTTPException(status_code=500, detail="Something Went Wrong")
