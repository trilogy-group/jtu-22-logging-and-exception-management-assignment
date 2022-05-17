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
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s: %(message)s")
filehandler = logging.FileHandler('db.log')
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)


@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)
    logger.info(f'post requested recieved for /reset_authkey with provider {provider} and role {role}')
    if role != "ADMIN" and (role != "3PL"):
        raise HTTPException(status_code=401, detail='Unauthorized access role is not ADMIN or 3PL') 
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    logger.info('post request accepted for /reset_authkey')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)
    logger.info(f'post requested recieved for /view_authkey with provider {provider} and role {role}')

    if role != "ADMIN" and role != "3PL":
        raise HTTPException(status_code=401, detail='Unauthorized access role is not ADMIN or 3PL') 
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    logger.info('post request accepted for /reset_authkey')
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
