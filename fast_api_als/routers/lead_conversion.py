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

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

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
    logging.info(f"Initiated S3 data conversion for item with lead UUID {lead_uuid}")
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
    logging.info(f"S3 data conversion of item with lead UUID {lead_uuid} successful")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    logging.info("Lead conversion request")
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))
    if 'lead_uuid' not in body or 'converted' not in body:
        logging.info("Lead conversion request terminated due to missing info")
        raise HTTPException(status_code=400, detail = "Missing information in body")
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        log.error("Lead conversion request terminated: insufficient role for oem {oem}")
        raise HTTPException(status_code=401, detail = "Unauthorized OEM")
        pass

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logging.info(f"Lead conversion is successful for item with uuid {lead_uuid}")
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        logging.error{f"Lead conversion request terminated: item with uuid {lead_uuid} is already updated"}
        raise HTTPException(status_code=400, detail = "Lead data already updated")
        pass
