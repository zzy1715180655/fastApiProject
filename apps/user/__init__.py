import requests
from fastapi import APIRouter, Request

import models
from utils import generate_token

router = APIRouter()


@router.get("/login")
async def login(code: str, request: Request):
    db = request.state.db
    try:
        res = requests.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": "wxa4f8f0622653dea5",
                "secret": "1936d0ddc00843ad1bf039907fb0f649",
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
    except Exception as e:
        print(e)
        return {"code": 201, "message": e.args}
    token = generate_token()
    openid = res.json()["openid"]
    # 如果该openid不存在 则保存到数据库
    db_user = db.query(models.User).filter_by(openid=openid).first()
    if db_user is None:
        db_user = models.User(openid=openid, token=token)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"code": 200, "data": {"token": token}}
    else:
        db_user.token = token
        db.commit()
        db.refresh(db_user)
        return {"code": 201, "data": {"token": token}}


# 根据token获取用户信息
@router.get("/api/getUserInfoByToken")
async def get_user_info_by_token(token: str, request: Request):
    db = request.state.db
    db_user = db.query(models.User).filter_by(token=token).first()
    if db_user:
        return {"code": 200, "data": db_user}
    else:
        return {"code": 201, "message": "用户未登录"}
