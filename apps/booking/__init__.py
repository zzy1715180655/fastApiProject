# 预约
from fastapi import Body, APIRouter
from pydantic import BaseModel
from starlette.requests import Request

import models
import schemas

router = APIRouter()


@router.post("/api/toBooking")
async def toBooking(request: Request, booking: schemas.Booking = Body(...)):
    # 验证token
    db = request.state.db
    db_user = db.query(models.User).filter_by(token=booking.token).first()
    # 判断用户是否存在
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}
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
    # 判断会议室是否可用
    if meeting_room.is_delete == 1:
        return {"code": 201, "message": "会议室不可用"}
    print(booking)
    # 生成预约记录
    db_booking = models.Booking(
        booking_meeting_room_id=booking.meeting_room_id,
        booking_user_id=db_user.id,
        booking_remark=booking.booking_remark,
        booking_date=booking.booking_date,
        booking_start_time=booking.booking_start_time,
        booking_end_time=booking.booking_end_time,
        booking_status=0,
    )
    try:
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return {"code": 200, "message": db_booking}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


class BookingStatus(BaseModel):
    # 审核人id
    approval_id: int | None
    # 审核时间
    approval_time: str | None


# 修改预约状态的pydantic模型
class UpdateBookingStatusItem(BaseModel):
    # 预约id
    booking_id: int
    # 预约状态 0:未审核 1:审核通过 2:审核不通过
    booking_status: int
    # 审核
    booking_approval: BookingStatus | None


# 更新预约状态
@router.post("/api/updateBookingStatus")
async def update_booking_status(
        request: Request,
        update_book_status_item: UpdateBookingStatusItem
):
    db = request.state.db
    user = request.state.user
    # 判断是否是超级管理员
    if user.role == 0:
        return {"code": 201, "message": "您不是超级管理员"}
    # 查询预约信息
    db_booking = (
        db.query(models.Booking)
        .filter_by(id=update_book_status_item.booking_id)
        .first()
    )
    # 更新预约状态
    db_booking.booking_status = update_book_status_item.booking_status
    try:
        db.commit()
        db.refresh(db_booking)
        return {"code": 200, "message": db_booking}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


# 获取预约反馈消息
@router.get("/api/getBookingMessageList")
async def get_booking_message_list(
        request: Request,
        page: int = None,
        page_size: int = None,
):
    db = request.state.db
    user = request.state.user
    # 获取预约总数
    booking_message_count = db.query(models.Booking).count()
    # 获取预约列表
    booking_message_list = (
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
            "booking_message_list": {"booking_room_name": booking_message_list},
            "booking_message_count": booking_message_count,
        },
    }


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
