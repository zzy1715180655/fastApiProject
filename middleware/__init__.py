# 写一个验证token的中间件
import time

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from database import SessionLocal
from models import User

app = FastAPI()

# 设置白名单
whitelist = ["/api/login", "/docs", "/openapi.json", "/redoc"]


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
    print(request.url.path)
    if str(request.url.path) in whitelist:
        print(request.url.path)
        return await call_next(request)
    token = request.headers.get('token', None)
    if not token:
        return Response(content="Missing token", status_code=401)
    db = request.state.db
    user = db.query(User).filter_by(token=token).first()
    if not user:
        return Response(content="Invalid token", status_code=401)
    request.state.user = user
    response = await call_next(request)
    return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Request: {request.method} {request.url}{time.time()}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response
