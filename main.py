import uvicorn
from fastapi import FastAPI, Depends, Body
# 跨域
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

import models
import schemas
from apps import meeting
from database import engine, origins
from middleware import get_db, db_session_middleware, verify_token

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
app.include_router(meeting.router, prefix="/api", tags=["user"])

# 调用创建的中间件
app.middleware("http")(verify_token)
app.middleware("http")(db_session_middleware)


# 根据传参进行个人信息修改,姓名,公司,头像
@app.post("/api/updateUserInfo")
async def update_user_info(
        update_user_info_item: schemas.UpdateUserInfoItem, db: Session = Depends(get_db)
):
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


# 根据日期查询会议室已经预约的时间段
@app.get("/api/getMeetingRoomOrderByDate")
async def get_meeting_room_order_by_date(
        meeting_room_id: int, order_date: str, token: str, db: Session = Depends(get_db)
):
    # 查询用户信息
    db_user = db.query(models.User).filter_by(token=token).first()
    # 判断用户是否存在
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}
    # 查询status为1的会议室信息
    db_meeting_room = (
        db.query(models.MeetingRoom)
        .filter_by(id=meeting_room_id)
        .filter_by(status=1)
        .first()
    )
    # 判断会议室是否存在
    if db_meeting_room is None:
        return {"code": 201, "message": "会议室不存在"}
    # 判断会议室是否可用
    if db_meeting_room.is_delete == 1:
        return {"code": 201, "message": "会议室不可用"}
    # 查询会议室预约信息
    db_meeting_room_order_list = (
        db.query(models.Booking)
        .filter_by(meeting_room_id=meeting_room_id)
        .filter_by(order_date=order_date)
        .all()
    )
    # 判断为空
    if db_meeting_room_order_list is None:
        return {"code": 201, "message": "会议室未被预约"}
    return {"code": 200, "message": db_meeting_room_order_list}


# 查看所有预约列表
@app.get("/api/getBookingList")
async def get_meeting_room_order_list(
        token: str,
        page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db),
):
    # 查询用户信息
    db_user = db.query(models.User).filter_by(token=token).first()
    # 判断用户是否存在
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}
    # 获取预约总数
    booking_count = db.query(models.Booking).count()
    # 获取预约列表
    booking_list = (
        db.query(models.Booking)
        .filter_by(booking_user_id=db_user.id)
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


# 预约
@app.post("/api/toBooking")
async def toBooking(booking: schemas.Booking = Body(...), db: Session = Depends(get_db)):
    # 验证token
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


# 修改预约状态的pydantic模型
class UpdateBookingStatusItem(BaseModel):
    booking_id: int
    booking_status: int
    token: str


# 更新预约状态
@app.post("/api/updateBookingStatus")
async def update_booking_status(
        update_book_status_item: UpdateBookingStatusItem, db: Session = Depends(get_db)
):
    # 查询用户信息
    db_user = (
        db.query(models.User).filter_by(token=update_book_status_item.token).first()
    )
    # 判断用户是否存在
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}
    # 判断是否是超级管理员
    if db_user.is_super == 0:
        return {"code": 201, "message": "您不是超级管理员"}
    # 查询预约信息
    db_booking = (
        db.query(models.Booking)
        .filter_by(id=update_book_status_item.booking_id)
        .first()
    )
    # 判断预约信息是否存在
    if db_booking is None:
        return {"code": 201, "message": "预约信息不存在"}
    # 判断预约信息是否属于该用户
    if db_booking.booking_user_id != db_user.id:
        return {"code": 201, "message": "预约信息不属于该用户"}
    # 更新预约状态
    db_booking.booking_status = update_book_status_item.booking_status
    # 更新审批人id
    db_booking.approval_id = db_user.id
    try:
        db.commit()
        db.refresh(db_booking)
        return {"code": 200, "message": db_booking}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}


# 获取预约反馈消息
@app.get("/api/getBookingMessageList")
async def get_booking_message_list(
        token: str,
        page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db),
):
    # 查询用户信息
    db_user = db.query(models.User).filter_by(token=token).first()
    # 判断用户是否存在
    if db_user is None:
        return {"code": 201, "message": "您已退出登录"}
    # 获取预约总数
    booking_message_count = db.query(models.Booking).count()
    # 获取预约列表
    booking_message_list = (
        db.query(models.Booking)
        .filter_by(booking_user_id=db_user.id)
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
@app.get("/api/getMeetingRoomOrderList")
async def get_meeting_room_order_list(
        meeting_room_id: int,
        page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db),
):
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


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", reload=True)
