import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        logger.info('Body of request parsed successfully')
    except Exception as e:
        logger.error(f'Parsing of body failed due to {e}')

    provider, role = get_user_role(token)
    logger.info(f'Reset authkey request from provider:{provider} having role: {role}')
    if role != "ADMIN" and (role != "3PL"):
        raise HTTPException(status_code=401, detail='User with role not ADMIN or 3PL not authorised to reset authkey')
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    logger.info(f'Returned apikey: {apikey} for request from provider:{provider} having role: {role}')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        logger.info('Body of request parsed successfully')
    except Exception as e:
        logger.error(f'Parsing of body failed due to {e}')
    
    provider, role = get_user_role(token)
    logger.info(f'Reset authkey request from provider:{provider} having role: {role}')

    if role != "ADMIN" and role != "3PL":
        raise HTTPException(status_code=401, detail='User with role not ADMIN or 3PL not authorised to view authkey')
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    logger.info(f'Returned apikey: {apikey} for request from provider:{provider} having role: {role}')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
