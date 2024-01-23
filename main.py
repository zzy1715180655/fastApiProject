from fastapi import FastAPI
# 跨域
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

import models
from apps import meeting, user
from database import engine, origins
from middleware import db_session_middleware, verify_token, LoggingMiddleware

# 创建表
# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")

# 路由
app.include_router(meeting.router, prefix="/api", tags=["meeting"])
app.include_router(user.router, prefix="/api", tags=["user"])
app.include_router(user.router, prefix="/api", tags=["booking"])

# 调用创建的中间件
app.add_middleware(LoggingMiddleware)
app.middleware("http")(verify_token)
app.middleware("http")(db_session_middleware)


# 修改预约状态的pydantic模型
class UpdateBookingStatusItem(BaseModel):
    booking_id: int
    booking_status: int
    token: str
