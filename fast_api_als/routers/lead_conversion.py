from http.client import HTTPException
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

# Creating and configuring logger
logging.basicConfig(filename="newFile.log",
                    format='%(asctime)s %(message)s', filemode='w')

# Creating an object logger
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


def get_quicksight_data(lead_uuid, item):
    """
            Creates the lead converted data for dumping into S3.
            Args:
                lead_uuid: Lead UUID
                item: Accepted lead info pulled from DDB
            Returns:
                S3 data
    """

    try:
        item['make']
    except:
        logger.error(
            "lead_conversion:def get_quicksight: no property named 'make' is present in the item parameter")
        raise Exception("Parameter Item does not have property named 'make'")

    try:
        item['model']
    except:
        logger.error(
            "lead_conversion:def get_quicksight: no property named 'model' is present in the item parameter")
        raise Exception("Parameter Item does not have property named 'model'")

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
    logger.info(
        "lead_conversion:def get_quicksight:This function ran successfully")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        # throw proper HTTPException
        pass
        logger.error(
            "lead_conversion:def submit:None among lead_uuid and converted is present in the body")
        raise HTTPException(
            400, detail="None among lead_uuid and converted is present in the body")

    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        # throw proper HTTPException
        pass
        logger.error("lead_conversion:def submit:Role is not equal to OEM")
        raise HTTPException(400, detail="Role is not equal to OEM")

    is_updated, item = db_helper_session.update_lead_conversion(
        lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        logger.info("lead_conversion:def submit:This function ran successfully")
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        pass
        logger.error("lead_conversion:def submit:Not updated")
        raise HTTPException(400, detail="Not Updated")
