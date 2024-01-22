# 会议室列表

from fastapi import Depends, APIRouter, Header
from sqlalchemy.orm import Session
from starlette.requests import Request

import models
import schemas
from middleware import get_db

# 创建路由
router = APIRouter()


# 获取会议室列表
@router.get(
    "/getMeetingRoomList",
    summary="获取会议室列表",
    # 允许传递header参数
    response_model=schemas.MeetingRoomList,

)
async def get_meeting_room_list(
        request: Request,
        token: str = Header(None),
        page: int = 1,
        page_size: int = 10,
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
        "code": 200,
        "data": {
            "meeting_room_list": meeting_room_list,
            "meeting_room_count": meeting_room_count,
        },
    }


# 新增会议室
@router.post("/api/addMeetingRoom", summary="新增会议室")
async def add_meeting_room(
        meeting: models.MeetingRoom,
        db: Session = Depends(get_db),
):
    db_meeting = models.MeetingRoom(
        name=meeting.name, capacity=meeting.capacity, image=meeting.avatar_url
    )
    try:
        db.add(db_meeting)
        db.commit()
        db.refresh(db_meeting)
        return {"code": 200, "message": db_meeting}
    except Exception as e:
        print(e)
        db.rollback()
        return {"code": 201, "message": e.args}
