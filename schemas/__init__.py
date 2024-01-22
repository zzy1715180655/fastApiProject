from typing import List

from pydantic import BaseModel


# 用户
class User(BaseModel):
    openid: int
    code: str
    name: str
    mobile: str
    company: str
    token: str
    is_delete: int


class UpdateUser(BaseModel):
    name: str
    company: str


# 会议室
class MeetingRoom(BaseModel):
    # 会议室名称
    name: str
    # 会议室容量
    capacity: int
    # 会议室图片
    avatar_url: str


class MeetingRoomList(BaseModel):
    meeting_room_list: List[MeetingRoom]
    meeting_room_count: int


# 预约
class Booking(BaseModel):
    meeting_room_id: int
    booking_user_id: int
    booking_remark: str
    booking_date: str
    booking_start_time: str
    booking_end_time: str
    booking_status: int = 0
    approval_id: int | None
    token: str


# 图片上传
class Image(BaseModel):
    file_path: str
    token: str
    meeting_room_id: int
    is_delete: int


class UpdateUserInfoItem(BaseModel):
    name: str
    token: str
    company: str
