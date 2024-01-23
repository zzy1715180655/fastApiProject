import requests
from fastapi import APIRouter, Request

import models
import schemas
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
@router.get("/api/getUserInfoByToken", summary="根据token获取用户信息")
async def get_user_info_by_token(token: str, request: Request):
    db = request.state.db
    db_user = db.query(models.User).filter_by(token=token).first()
    if db_user:
        return {"code": 200, "data": db_user}
    else:
        return {"code": 201, "message": "用户未登录"}


# 根据传参进行个人信息修改,姓名,公司,头像
@router.post("/api/updateUserInfo", summary="根据传参进行个人信息修改,姓名,公司,头像")
async def update_user_info(
        update_user_info_item: schemas.UpdateUserInfoItem,
        request: Request,
):
    db = request.state.db
    db_user = (
        db.query(models.User).filter_by(token=update_user_info_item.token).first()
    )
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}

    db_user.name = update_user_info_item.name
    db_user.company = update_user_info_item.company
    try:
        db.commit()
        db.refresh(db_user)
        return {"code": 200, "message": db_user}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


# 查看所有预约列表
@router.get("/api/getBookingList")
async def get_meeting_room_order_list(
        request: Request,
        page: int = None,
        page_size: int = None,
):
    db = request.state.db
    user = request.state.user
    # 获取预约总数
    booking_count = db.query(models.Booking).count()
    # 获取预约列表
    booking_list = (
        db.query(models.Booking)
        .filter_by(booking_user_id=user.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
        .all()
    )
    # 分页结构体
    # 返回数据
    return {
        "code": 200,
        "data": {
            "booking_list": booking_list,
            "booking_count": booking_count,
        },
    }
