# 会议室列表

from fastapi import APIRouter, Header, Request

import models
import schemas

# 创建路由
router = APIRouter()


# 获取会议室列表
@router.get(
    "/getMeetingRoomList",
    summary="获取会议室列表",
)
async def get_meeting_room_list(
        request: Request,
        page: int | None,
        page_size: int | None,
        token: str = Header(None, description="用户token"),
):
    db = request.state.db
    # 获取会议室列表
    meeting_room_list = (
        db.query(models.MeetingRoom)
        .limit(page_size)
        .offset((page - 1) * page_size)
        .all()
    )
    # 获取会议室总数
    meeting_room_count = db.query(models.MeetingRoom).count()
    # 返回数据
    return {
        "meeting_room_list": meeting_room_list,
        "meeting_room_count": meeting_room_count,
    }


# 新增会议室
@router.post(
    "/addMeetingRoom",
    summary="新增会议室",
    response_model=None
)
async def add_meeting_room(
        request: Request,
        meeting_room: schemas.MeetingRoom,
        token: str = Header(None, description="用户token"),
):
    db = request.state.db
    # 判断会议室是否存在
    db_meeting_room = (
        db.query(models.MeetingRoom)
        .filter_by(name=meeting_room.name)
        .first()
    )
    if db_meeting_room is not None:
        return {"code": 201, "message": "会议室已存在"}
    # 新增会议室
    db_meeting_room = models.MeetingRoom(
        name=meeting_room.name,
        capacity=meeting_room.capacity,
        status=0
    )
    try:
        db.add(db_meeting_room)
        db.commit()
        db.refresh(db_meeting_room)
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}
    return {"code": 200, "message": "新增成功"}


# 修改会议室
@router.put(
    "/updateMeetingRoom",
    summary="修改会议室",
    response_model=None
)
async def update_meeting_room(
        request: Request,
        meeting_room_id: int,
        meeting_room: schemas.MeetingRoom,
        token: str = Header(None, description="用户token"),
):
    db = request.state.db
    # 判断会议室是否存在
    db_meeting_room = (
        db.query(models.MeetingRoom)
        .filter_by(id=meeting_room_id)
        .first()
    )
    if db_meeting_room is None:
        return {"code": 201, "message": "会议室不存在"}
    # 修改会议室信息
    db_meeting_room.name = meeting_room.name
    db_meeting_room.capacity = meeting_room.capacity
    try:
        db.commit()
        db.refresh(db_meeting_room)
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}
    return {"code": 200, "message": "修改成功"}


# 根据日期查询会议室已经预约的时间段
@router.get("/getBookedTimeByDate", summary="根据日期查询会议室已经预约的时间段")
async def get_booked_time_by_date(
        meeting_room_id: int,
        order_date: str,
        request: Request,
        token: str = Header(None)
):
    db = request.state.db
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
