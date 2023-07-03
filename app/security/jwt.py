import asyncio
from typing import Annotated
from fastapi import Depends
from pydantic import BaseModel
from async_fastapi_jwt_auth import AuthJWT
from asyncio import AbstractEventLoop

from app.rds import check_token

Authorize = Annotated[AuthJWT, Depends(AuthJWT)]


class Settings(BaseModel):
    authjwt_secret_key: str = "secret"
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access"}


@AuthJWT.load_config
def get_config():
    return Settings()


@AuthJWT.token_in_denylist_loader
async def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token['jti']
    rs = await check_token(jti)
    return rs
