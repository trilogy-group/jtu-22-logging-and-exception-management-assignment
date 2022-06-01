import json
from fastapi import Request
from fast_api_als.utils.logger import logger

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
    logger.info(f"Provider {provider} with role {role} requested an auth key reset")
    if role != "ADMIN" and (role != "3PL"):
        logger.error(f"Provider {provider} has an insufficient role for auth key reset")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail = "User is unauthorized")
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.set_auth_key(username=provider)
    logger.info(f"Auth key reset successful for provider {provider} with role {role}")
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    start_time = time
    body = await request.body()
    body = json.loads(body)
    provider, role = get_user_role(token)
    logger.info(f"Provider {provider} with role {role} requested to view auth key")    
    if role != "ADMIN" and role != "3PL":
        logger.error(f"Provider {provider} has an insufficient role for viewing auth key")
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail = "User is unauthorized")
    if role == "ADMIN":
        provider = body['3pl']
    apikey = db_helper_session.get_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
