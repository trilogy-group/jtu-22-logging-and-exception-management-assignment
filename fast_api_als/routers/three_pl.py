import json
import logging
from fastapi import Request, HTTPException

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()

log = logging.getLogger(__name__)

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        log.info("Body parsed successfully.")
    except json.JSONDecodeError as jde : 
        log.error(f'Request body not a valid JSON document: {jde}')
    except Exception as e:
        log.error(f'Request body parse failed: {e}')
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        raise HTTPException(status_code=401, detail='User with role other than ADMIN or 3PL are not authorized.')
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    log.info(f'Successfully set the API auth key for the user :{provider} having role: {role}')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    try:
        body = await request.body()
        body = json.loads(body)
        log.info('Request body parsed successfully.')
    except json.JSONDecodeError as jde:
        log.error(f'Request body is not a valid JSON document: {jde}')
    except Exception as e:
        log.error(f'Parsing of request body failed: {e}')
    provider, role = get_user_role(token)

    if role != "ADMIN" and role != "3PL":
        raise HTTPException(status_code=401, detail='User with role other than ADMIN or 3PL are not authorized.')
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    log.info(f'Successfully set the API auth key for the user :{provider} having role: {role}')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
