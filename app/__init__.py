import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.rds import REDIS_URL, add_token, check_token
from app.auth import router
from app.post import router as posts_router

from async_fastapi_jwt_auth.exceptions import AuthJWTException


app = FastAPI()


@app.exception_handler(Exception)
def exception_handler(request: Request, exc: Exception):
    match exc:
        case AuthJWTException(status_code=exc.status_code,
                              message=exc.message):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message}
            )
        case _:
            return JSONResponse(
                status_code=400,
                content={"message": "Unhandled exception, check logs"}
            )


app.include_router(router)
app.include_router(posts_router)
