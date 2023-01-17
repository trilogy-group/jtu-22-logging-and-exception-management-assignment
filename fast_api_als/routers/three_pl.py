import json
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException, Depends
    from fast_api_als.database.db_helper import db_helper_session
    from fast_api_als.services.authenticate import get_token
    from fast_api_als.utils.cognito_client import get_user_role
    from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
except:
    raise ImportError("Import Error in submit_lead.py from fast_api_als")
    logger.error("Import Error in submit_lead.py from fast_api_als")


router = APIRouter()

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):

    try:    
        startTime = time.time()
        logger.info("Waiting for Request Body")
        body = await file.body()
        endTime = time.time()
        elapsedTime = (endTime-startTime)*1000
        logger.info(f"Request Body arrived in {elapsedTime} ms")
        
    except:
        raise HTTPException(status_code=400, detail="Bad request. Request body did not arrive in three_pl.py while resetting the key") 
        logger.error("Bad request. Request body did not arrive in three_pl.py while resetting the key")   

    body = json.loads(body)
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        logger.info("Role received in three_pl.py is neither ADMIN nor 3PL")
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    logger.info("Setting Auth key")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    try:    
        startTime = time.time()
        logger.info("Waiting for Request Body")
        body = await file.body()
        endTime = time.time()
        elapsedTime = (endTime-startTime)*1000
        logger.info(f"Request Body arrived in {elapsedTime} ms")
        
    except:
        raise HTTPException(status_code=400, detail="Bad request. Request body did not arrive in three_pl.py while viewing the key") 
        logger.error("Bad request. Request body did not arrive in three_pl.py while viewing the key")   

    body = json.loads(body)
    provider, role = get_user_role(token)

    if role != "ADMIN" and role != "3PL":
        logger.info("Role received in three_pl.py is neither ADMIN nor 3PL")
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
