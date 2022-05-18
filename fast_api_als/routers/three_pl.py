import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()

logging.basicConfig(filename='test.log', level=logging.INFO,
format='%(asctime)s:%(levelname)s:%(message)s')

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    body = json.loads(body)
    logging.info("body recieved  is "+body)
    try :
        provider, role = get_user_role(token)
    except:
        logging.error("provider / role is undefined ")
    logging.info("provider and role are "+provider+role)
    
    if role != "ADMIN" and (role != "3PL"):
        raise HTTPException(
            status_code=401,detail="Unauthorized")
    if role == "ADMIN":
        provider = body['3pl']
        if not provider:
            logging.warning("provider is not defined ")
        else :
            logging.info("provider is defined")
    apikey = db_helper_session.set_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    body = await request.body()
    logging.info("body recieved is "+body)
    
    body = json.loads(body)
    try :
        provider, role = get_user_role(token)
    except:
        logging.error("provider / role is undefined")
    logging.info("provider and role  are "+provider+role)

    if role != "ADMIN" and role != "3PL":
        raise HTTPException(
            status_code=401,detail="Unauthorized")
    if role == "ADMIN":
        provider = body['3pl']
        if not provider:
            logging.warning("provider is not defined")
    apikey = db_helper_session.get_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
