import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()


@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    try:
        body = json.loads(body)
    except ValueError:
        logging.error("JSON format invalid")
        raise ValueError
    provider, role = get_user_role(token)
    logging.debug("Provider, role = "+provider+", "+role)
    if role != "ADMIN" and (role != "3PL"):
        logging.error("Role required to be admin or 3PL")
        raise HTTPException(status_code = 400, detail = "Role required to be admin or 3PL")
    if role == "ADMIN":
        logging.info("Role is Admin, updating provider to 3PL")
        provider = body['3pl']
    
    logging.info("Trying to update API key")
    try:
        apikey = db_helper_session.set_auth_key(username=provider)
        logging.debug("API key "+apikey)
    except Exception as e:
        logging.error("API key not set:"+str(e.message))
        raise e
    logging.info("Successfully updated API key")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    try:
        body = json.loads(body)
    except ValueError:
        logging.error("JSON format invalid")
        raise ValueError
    provider, role = get_user_role(token)
    logging.debug("Provider, role = "+provider+", "+role)
    if role != "ADMIN" and (role != "3PL"):
        logging.error("Role required to be admin or 3PL")
        raise HTTPException(status_code = 400, detail = "Role required to be admin or 3PL")
    if role == "ADMIN":
        logging.info("Role is Admin, updating provider to 3PL")
        provider = body['3pl']
    
    logging.info("Trying to get API key")
    try:
        apikey = db_helper_session.get_auth_key(username=provider)
        logging.debug("API key "+apikey)
    except Exception as e:
        logging.error("API key not found:"+str(e.message))
        raise e
    logging.info("Successfully found API key")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
