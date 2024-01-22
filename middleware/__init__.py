# 写一个验证token的中间件

from fastapi import FastAPI, Header
from starlette.requests import Request
from starlette.responses import Response

from database import SessionLocal
from models import models

app = FastAPI()

# 设置白名单
whitelist = ["/api/login", "/docs", "/openapi.json", "/redoc"]


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    print(type(response))
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
        print(type(response))
    finally:
        request.state.db.close()
    return response


async def get_db(request: Request):
    return request.state.db


@app.middleware("http")
async def verify_token(request: Request, token: Header(...), call_next):
    if request.url.path not in whitelist:
        response = await call_next(request)
        return response
    else:
        db = request.state.db
        user = db.query(models.User).filter_by(token=token).first()
        if not user:
            return Response(content="用户未登录", status_code=201)
        else:
            response = await call_next(request)
            return response
