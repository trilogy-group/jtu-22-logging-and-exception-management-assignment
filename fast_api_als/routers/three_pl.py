import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()

logging.basicConfig(filename = 'logs.log' , level = logging.INFO , format = '%(asctime)s : %(filename)s : %(lineno)d :: %(levelno)s : %(message)s')


@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)

    logging.info('viewinf authkey...')
    if role != "ADMIN" and role != "3PL":
        try : 
            raise HTTPException(status_code=401, detail="Precondition failed! Role neither ADMIN nor 3PL")
        except : 
            logging.error(' ',exc_info = True)
        pass
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
