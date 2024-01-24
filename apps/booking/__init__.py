# 预约
from fastapi import APIRouter, Header
from starlette.requests import Request

import models
import schemas

router = APIRouter()


# 预约会议室
@router.post("/booking", summary="预约会议室")
async def toBooking(
        request: Request,
        booking: schemas.Booking,
        token: str = Header()
):
    db = request.state.db
    user = request.state.user
    # 其中还需要一些判断是否能预约的操作
    # 查询会议室信息
    meeting_room = (
        db.query(models.MeetingRoom)
        .filter_by(id=booking.meeting_room_id)
        .first()
    )
    # 判断会议室是否存在
    if meeting_room is None:
        return {"code": 201, "message": "会议室不存在"}
    # 生成预约记录
    db_booking = models.Booking(
        booking_meeting_room_id=booking.meeting_room_id,
        booking_user_id=user.id,
        booking_remark=booking.booking_remark,
        booking_date=booking.booking_date,
        booking_start_time=booking.booking_start_time,
        booking_end_time=booking.booking_end_time,
    )
    # 修改会议室状态
    meeting_room.status = 1
    try:
        db.add(db_booking, meeting_room)
        db.commit()
        db.refresh(db_booking)
        return {
            "code": 200,
            "data": {
                "booking_meeting_room_id": db_booking.booking_meeting_room_id,
                "booking_user_id": user.id,
                "booking_remark": db_booking.booking_remark,
                "booking_date": db_booking.booking_date,
                "booking_start_time": db_booking.booking_start_time,
                "booking_end_time": db_booking.booking_end_time,

            }
        }
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


# 更新预约状态
@router.put("/bookingStatus", summary="更新预约状态")
async def booking_status(
        request: Request,
        meeting_room_id: int,
        meeting_room_status: int,
        token: str = Header(),
):
    db = request.state.db
    user = request.state.user
    # 判断是否是超级管理员
    if user.role == 0:
        return {"code": 201, "message": "您不是超级管理员"}
    # 查询预约信息
    db_booking = (
        db.query(models.Booking)
        .filter_by(id=meeting_room_id)
        .first()
    )
    # 更新预约状态
    db_booking.booking_status = meeting_room_status
    try:
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return {
            "code": 200,
            "data": {
                "meeting_room_id": meeting_room_id,
                "meeting_room_status": meeting_room_status,
            }
        }
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


# 获取预约列表
@router.get("/bookingList", summary="获取预约列表")
async def booking_list(
        request: Request,
        meeting_room_id: int,
        meeting_room_status: int,
        token: str = Header(),
        page: int = None,
        page_size: int = None,
):
    db = request.state.db
    user = request.state.user
    # 判断是否是超级管理员
    if user.role == 0:
        return {"code": 201, "message": "您不是超级管理员"}
    # 获取预约总数
    count = db.query(models.Booking).count()
    # 获取预约列表
    result = (
        db.query(
            models.Booking.booking_remark,
            models.Booking.booking_date,
            models.Booking.booking_start_time,
            models.Booking.booking_end_time,
            models.User.name,
        )
        .join(models.User, models.Booking.booking_user_id == models.User.id)
        .filter(models.Booking.booking_meeting_room_id == meeting_room_id,
                models.Booking.booking_status == meeting_room_status)
        .limit(page_size)
        .offset((page - 1) * page_size)
        .all()
    )

    result = [
        {
            "booking_remark": row.booking_remark,
            "booking_date": row.booking_date,
            "booking_start_time": row.booking_start_time,
            "booking_end_time": row.booking_end_time,
            "name": row.name,
        }
        for row in result
    ]
    # 返回数据
    return {
        "code": 200,
        "data": {
            "booking_list": result,
            "count": count,
        },
    }
