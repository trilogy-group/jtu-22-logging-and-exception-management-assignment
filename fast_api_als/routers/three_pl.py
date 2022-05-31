import logging

logging.basicConfig(
    level = logging.INFO,
    format = "{asctime} {levelname:<8} {message}",
    style= '{',
    filename = 'fast_api_als.log',
    filemode = 'a'
)
try:

    import json
    from fastapi import Request

    from fastapi import APIRouter, HTTPException, Depends
    from fast_api_als.database.db_helper import db_helper_session
    from fast_api_als.services.authenticate import get_token
    from fast_api_als.utils.cognito_client import get_user_role
    from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
except ImportError as e:
    logging.error("Import Error occured", exc_info=True)

router = APIRouter()


@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    logging.info("Awaiting request body")
    body = await request.body()
    logging.info("Received request body")
    body = json.loads(body)
    provider, role = get_user_role(token)
    if role != "ADMIN" and (role != "3PL"):
        logging.warning("Role received was neither an Admin nor 3PL")
        pass
    if role == "ADMIN":
        provider = body['3pl']
        logging.info("Setting auth key")
    apikey = db_helper_session.set_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    logging.info("Viewing auth key")
    logging.info("Awaiting request body")
    body = await request.body()
    logging.info("Received request body")
    body = json.loads(body)
    provider, role = get_user_role(token)

    if role != "ADMIN" and role != "3PL":
        logging.warning("role received was neither and admin nor 3PL")
        pass
    if role == "ADMIN":
        logging.info("Role received was admin")
        provider = body['3pl']
        logging.info("Getting auth key")
    apikey = db_helper_session.get_auth_key(username=provider)
    return {
        "status_code": HTTP_200_OK,
        "x-api-key": apikey
    }
