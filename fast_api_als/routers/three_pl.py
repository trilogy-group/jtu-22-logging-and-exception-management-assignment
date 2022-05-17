import json
import logging
import time

from fastapi import Request
from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()


@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):

    logging.info("Recieving data")
    t1 = (int)(time.time()*1000)
    body = await request.body()
    t2 = int(time.time()*1000.0)
    logging.info(f'Recieved data in {t2-t1} ms.')

    try:
        body = json.loads(body)
    except:
        logging.error("Unable to load data")
        raise HTTPException(status_code=500, detail="Unable to load data")
    
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        logging.error("User not authorised")
        raise HTTPException(status_code=401, detail="User not authorised")
    if role == "ADMIN":
        provider = body['3pl']
    try:
        apikey = db_helper_session.set_auth_key(username=provider)
    except:
        logging.error("Unable to set apikey")
        raise HTTPException(status_code=500, detail="Unable to set apikey")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):

    logging.info("Recieving data")
    t1 = (int)(time.time()*1000)
    body = await request.body()
    t2 = int(time.time()*1000.0)
    logging.info(f'Recieved data in {t2-t1} ms.')

    try:
        body = json.loads(body)
    except:
        logging.error("Unable to load data")
        raise HTTPException(status_code=500, detail="Unable to load data")
    
    provider, role = get_user_role(token)

    if role != "ADMIN" and (role != "3PL"):
        logging.error("User not authorised")
        raise HTTPException(status_code=401, detail="User not authorised")

    if role == "ADMIN":
        provider = body['3pl']
    try:
        apikey = db_helper_session.get_auth_key(username=provider)
    except:
        logging.error("Unable to get apikey")
        raise HTTPException(status_code=500, detail="Unable to get apikey")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
