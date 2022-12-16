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
    logging.info("Parsing body")
    body = await request.body()
    body = json.loads(body)
    logging.info("Getting user role")
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        logging.error(f"Unauthorized {role}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"{role} not allowed to post")
    if role == "ADMIN":
        provider = body['3pl']
    logging.info("Setting auth key")
    apikey = db_helper_session.set_auth_key(username=provider)
    logging.info("Respoding 200 OK")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    logging.info("Parsing body")
    body = await request.body()
    body = json.loads(body)
    logging.info("Getting user role")
    provider, role = get_user_role(token)

    if role != "ADMIN" and role != "3PL":
        logging.error(f"Unauthorized {role}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"{role} not allowed to post")
    if role == "ADMIN":
        provider = body['3pl']
    logging.info("Setting auth key")
    apikey = db_helper_session.get_auth_key(username=provider)
    logging.info("Respoding 200 OK")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
