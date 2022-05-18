import json
from fastapi import APIRouter, Depends
from logging import info, error,getLogger,warning
import time

from fastapi import Request
from starlette import status

from fast_api_als.database.db_helper import db_helper_session
# from fast_api_als.quicksight.s3_helper import s3_helper_client
from fast_api_als.services.authenticate import get_token
# from fast_api_als.utils.cognito_client import get_user_role

router = APIRouter()

basicConfig(filename='logfile2.log',level = DEBUG , style= '{', format = "{name} || {asctime} || {message}")
logger =  getLogger("man")

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
    logger.info("accepting Lead info pulled from DDB")
    logger.info("lead_hash " +data[lead_hash] + " model " + data[model] + " postalcode " +postalcode + " dealer " + dealer)
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    start_time = time.time()
    body = await file.body()
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
            # throw proper HTTPException
        exception("lead_uuid or converted doesn't exist in submited file")
        pass
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    role = "OEM"
    oem = "oem"
    # oem, role = get_user_role(token)
    if role != "OEM":
        exception
        pass

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        # s3_helper_client.put_file(data, path)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
        logger.info("file is updated time taken : " + (time.time() - start_time))

    else:
        logger.error("there was an error while updating Lead conversion time taken : " + (time.time() - start_time))
        raise HTTPException(status_code=500, detail="counter an error while updating lead conversation")
        pass
