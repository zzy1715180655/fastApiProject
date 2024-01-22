# 写一个验证token的中间件

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from database import SessionLocal
from models import User

app = FastAPI()

# 设置白名单
whitelist = ["/login", "/docs", "/openapi.json", "/redoc"]


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


async def get_db(request: Request):
    return request.state.db


@app.middleware("http")
async def verify_token(request: Request, call_next):
    if str(request.url.path) in whitelist:
        return await call_next(request)
    token = request.headers.get('Authorization', None)
    if not token:
        return Response(content="Missing token", status_code=401)
    db = request.state.db
    user = db.query(User).filter_by(token=token).first()
    if not user:
        return Response(content="Invalid token", status_code=401)
    request.state.user = user
    response = await call_next(request)
    return response
