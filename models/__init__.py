from fastapi import APIRouter
from sqlalchemy import Column, Integer, String
from starlette.requests import Request

import models
from database import Base

router = APIRouter()


# 分页结构体
class Pagination:
    def __init__(self, page: int, page_size: int):
        self.page = page
        self.page_size = page_size


# 查询某个会议室的所有现存预约
@router.get("/api/getMeetingRoomOrderList")
async def get_meeting_room_order_list(
        request: Request,
        meeting_room_id: int,
        page: int = 1,
        page_size: int = 10,
):
    db = request.state.db
    # 获取预约总数
    booking_count = db.query(models.Booking).count()
    # 获取预约列表
    booking_list = (
        db.query(models.Booking)
        .filter_by(meeting_room_id=meeting_room_id)
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # 用户姓名
    name = Column(String(50), default="")
    # 用户微信openid
    openid = Column(String(50), default="")
    # code
    code = Column(String(50), default="")
    # 用户手机号
    mobile = Column(String(20), default="")
    # 用户公司
    company = Column(String(50), default="")
    # 头像地址
    avatar_url = Column(String(200), default="")
    # token
    token = Column(String(50), default="")
    # 是否是超级管理员
    role = Column(Integer, default=0)
    # 是否删除 0:未删除 1:已删除
    is_delete = Column(Integer, default=0)


class MeetingRoom(Base):
    __tablename__ = "meeting_rooms"
    # 会议室id
    id = Column(Integer, primary_key=True, index=True)
    # 会议室名称
    name = Column(String(50), default="", unique=True)
    # 会议室容量
    capacity = Column(Integer, default=0)
    # 会议室图片
    avatar_url = Column(String(200), default="")
    # 会议室状态 0:空闲 1:预约中 2:使用中
    status = Column(Integer, default=0)
    # 是否删除 0:未删除 1:已删除
    is_delete = Column(Integer, default=0)


# 预约
class Booking(Base):
    __tablename__ = "booking"

    id = Column(Integer, primary_key=True, index=True)
    # 会议室id
    booking_meeting_room_id = Column(Integer, default=0)
    # 预约人id
    booking_user_id = Column(Integer, default=0)
    # 预约备注
    booking_remark = Column(String(200), default="")
    # 预约日期
    booking_date = Column(String(20), default="")
    # 预约开始时间
    booking_start_time = Column(String(20), default="")
    # 预约结束时间
    booking_end_time = Column(String(20), default="")
    # 预约状态 0:未审核 1:审核通过 2:审核不通过
    booking_status = Column(Integer, default=0)
    # 审核人id
    approval_id = Column(Integer, default=0)
    # 是否删除 0:未删除 1:已删除
    is_delete = Column(Integer, default=0)
