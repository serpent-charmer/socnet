from hashlib import sha1
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from async_fastapi_jwt_auth.exceptions import MissingTokenError
from pydantic import BaseModel
from sqlalchemy import and_, insert, select
from sqlalchemy.exc import IntegrityError
from app.rds import add_token, revoke_token
from app.security.jwt import Authorize
from db.models import SocUser
from db.session import SessionDependency


class UserData(BaseModel):
    login: str
    pswd: str
    name: str
    email: str


class LogoutData(BaseModel):
    token: str


async def check_email(email):
    return True


def get_pwd(pwd_str: str):
    return sha1(pwd_str.encode("utf-8"))


router = APIRouter(prefix="/account",
                   tags=["account"])


@router.post("/signup")
async def signup(data: UserData, sess: SessionDependency):
    if not await check_email(data.email):
        return JSONResponse(status_code=400,
                            content={"message": "Email doesn't exists"})
    enc = get_pwd(data.pswd)
    try:
        await sess.execute(insert(SocUser).values(login=data.login,
                                                  name=data.name,
                                                  email=data.email,
                                                  pswd=enc.hexdigest()))
        await sess.commit()
        u = router.url_path_for("login")
        return RedirectResponse(u)
    except IntegrityError:
        return JSONResponse(status_code=400,
                            content={"message": "Pick another name"})


@router.post("/login")
async def login(data: UserData, sess: SessionDependency, auth: Authorize):
    await auth.jwt_optional()

    subj = await auth.get_jwt_subject()
    if subj is not None:
        return JSONResponse(status_code=400,
                            content={"message": "Already logged in"})

    enc = get_pwd(data.pswd)
    usr = await sess.execute(select(SocUser)
                             .where(and_(SocUser.login == data.login,
                                         SocUser.pswd == enc.hexdigest())))

    if usr.scalar_one_or_none() is not None:
        access_token = await auth.create_access_token(subject=data.login)
        jti = await auth.get_jti(access_token)
        await add_token(jti)
        return {"access_token": access_token}
    else:
        return JSONResponse(status_code=400,
                            content={"message": "Wrong credentials"})


@router.post("/logout")
async def logout(auth: Authorize):
    await auth.jwt_required()

    token = await auth.get_raw_jwt()
    if token is not None:
        await revoke_token(token['jti'])
