import logging

logging.basicConfig(
    level = logging.INFO,
    format = "{asctime} {levelname:<8} {message}",
    style= '{',
    filename = 'fast_api_als.log',
    filemode = 'a'
)
try:
    import json
    from fastapi import APIRouter, Depends
    import time

    from fastapi import Request
    from starlette import status

    from fast_api_als.database.db_helper import db_helper_session
    from fast_api_als.quicksight.s3_helper import s3_helper_client
    from fast_api_als.services.authenticate import get_token
    from fast_api_als.utils.cognito_client import get_user_role
except ImportError as e:
    logging.error("Import Exception Occurred:", exc_info = True)
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
    logging.info("Data converted for dumping into S3")
    return data, f"{item['make']}/1_{int(time.time())}_{lead_uuid}"


@router.post("/conversion")
async def submit(file: Request, token: str = Depends(get_token)):
    logging.info("Waiting Request body")
    body = await file.body()
    logging.info("Request body received")
    body = json.loads(str(body, 'utf-8'))

    if 'lead_uuid' not in body or 'converted' not in body:
        logging.error("The HTTP request received does not contiane either lead_uuid or converted")
        raise HTTPException(status_code= HTTP_400_BAD_REQUEST, detail="Improper response received")
        pass
        
    lead_uuid = body['lead_uuid']
    converted = body['converted']

    oem, role = get_user_role(token)
    if role != "OEM":
        logging.error("The request received does not have the required permissions")
        raise HTTPException(status_code= HTTP_403_FORBIDDEN, detail= "The request received does not have the required permissions")
        pass

    is_updated, item = db_helper_session.update_lead_conversion(lead_uuid, oem, converted)
    if is_updated:
        data, path = get_quicksight_data(lead_uuid, item)
        s3_helper_client.put_file(data, path)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Lead Conversion Status Update"
        }
    else:
        # throw proper HTTPException
        logging.error("Lead Conversion could not take place")
        raise HTTPException(status_code = HTTP_404_NOT_FOUND, detail= "Excpetion occured while lead conversion")
        pass
