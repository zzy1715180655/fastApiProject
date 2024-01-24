import requests
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel

import models
from utils import generate_token

router = APIRouter()


@router.get("/login", summary="登录")
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
@router.get("/getUserInfoByToken", summary="根据token获取用户信息")
async def get_user_info_by_token(request: Request, token: str = Header()):
    user = request.state.user
    if user:
        return {"code": 200, "data": {"name": user.name, "company": user.company, "mobile": user.mobile}}
    else:
        return {"code": 201, "message": "用户未登录"}


class UpdateUserInfoItem(BaseModel):
    name: str
    company: str


# 根据传参进行个人信息修改,姓名,公司,头像
@router.post("/updateUserInfo", summary="根据传参进行个人信息修改,姓名,公司,头像")
async def update_user_info(
        update_user_info_item: UpdateUserInfoItem,
        request: Request,
        token: str = Header(),
):
    db = request.state.db
    user = request.state.user
    user.name = update_user_info_item.name
    user.company = update_user_info_item.company
    try:
        db.commit()
        db.refresh(user)
        return {"code": 200, "data": {
            "name": user.name,
            "mobile": user.mobile,
            "company": user.company,
        }}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}
