import json
import logging
from fastapi import Request

from fastapi import APIRouter, HTTPException, Depends
from fast_api_als.database.db_helper import db_helper_session
from fast_api_als.services.authenticate import get_token
from fast_api_als.utils.cognito_client import get_user_role
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

router = APIRouter()

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

@router.post("/reset_authkey")
async def reset_authkey(request: Request, token: str = Depends(get_token)):
    start = int(time.time() * 1000.0)
    try:
        logging.info("Reset Auth Key Request")
        body = await request.body()
        body = json.loads(body)

        logging.info("Checking Required permissions")
        provider, role = get_user_role(token)
        if role != "ADMIN" and (role != "3PL"):
            time_taken = int(time.time() * 1000.0) - start
            logging.info(f"Permission Missing : Auth Key Reset Request Terminated in {time_taken}ms")
            raise HTTPException(status_code=403,detail="You do not have required permission")
            # pass
        if role == "ADMIN":
            provider = body['3pl']

        logging.info("Setting Auth Key")
        apikey = db_helper_session.set_auth_key(username=provider)
        time_taken = int(time.time() * 1000.0) - start
        logging.info(f"Auth Key Resetted in {time_taken}ms")
        return {
            "status_code": HTTP_200_OK,
            "x-api-key": apikey
        }
    except as e:
        logging.error(f"AuthKey Reset Failed: {e.message}")
        raise HTTPException(status_code=500,detail="Something Went Wrong")


@router.post("/view_authkey")
async def view_authkey(request: Request, token: str = Depends(get_token)):
    start = int(time.time() * 1000.0)
    try:
        logging.info("View Auth Key Request")
        body = await request.body()
        body = json.loads(body)

        logging.info("Checking Required permissions")
        provider, role = get_user_role(token)

        if role != "ADMIN" and role != "3PL":
            time_taken = int(time.time() * 1000.0) - start
            logging.info(f"Permission Missing : Auth Key Fetch Request Terminated in {time_taken}ms")
            raise HTTPException(status_code=403,detail="You do not have required permissions")
            # pass
        if role == "ADMIN":
            provider = body['3pl']

        logging.info("Getting Auth Key")
        apikey = db_helper_session.get_auth_key(username=provider)
        time_taken = int(time.time() * 1000.0)
        logging.info(f"Auth Key Returned in {time_taken}ms")
        return {
            "status_code": HTTP_200_OK,
            "x-api-key": apikey
        }
    except as e:
        logging.error(f"AuthKey View Request Failed: {e.message}")
        raise HTTPException(status_code=500,detail="Something Went Wrong")
