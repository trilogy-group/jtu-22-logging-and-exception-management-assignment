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
    body = json.loads(body)
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        logging.info("Role is neither Admin nor 3PL")
        pass
    if role == "ADMIN":
        logging.info("Role is Admin")
        provider = body['3pl']
    try:
        apikey = db_helper_session.set_auth_key(username=provider)
    except Exception as e:
        logging.error("API key not set:"+str(e.message))
        raise e
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)

    if role != "ADMIN" and (role != "3PL"):
        logging.info("Role is neither Admin nor 3PL")
        pass
    if role == "ADMIN":
        logging.info("Role is Admin")
        provider = body['3pl']
    try:
        apikey = db_helper_session.get_auth_key(username=provider)
    except Exception as e:
        logging.error("API key not found:"+str(e.message))
        raise e
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
