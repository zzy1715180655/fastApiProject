import os
import time

from fastapi import APIRouter, UploadFile
from fastapi.params import Form, File, Depends
from sqlalchemy.orm import Session

from middleware import get_db
from models import models

router = APIRouter()


# 图片上传/保存
@router.post("/api/upLoadImage", summary="图片上传/保存")
async def upload_image(
    token: str = Form(),
    meeting: int = Form(),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # 如果meeting字段为1  则保存为会议室图片
        if meeting == 1:
            # 保存图片
            file_path = "static/meeting_room/" + file.filename + str(int(time.time()))
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            # 保存图片路径
            return {"code": 200, "url": file_path}
        elif meeting == 0:
            # 获取用户信息
            db_user = db.query(models.User).filter_by(token=token).first()
            # 判断用户是否存在
            if db_user is None:
                return {"code": 201, "message": "您已退出登录"}
            # 查询原图片地址,删除原有头像
            if db_user.avatar_url:
                os.remove(db_user.avatar_url)
            # 保存图片,时间戳+文件名
            file_path = "static/avatar/" + file.filename + str(int(time.time()))
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            # 保存图片路径l
            db_user.avatar_url = file_path
            db.commit()
            db.refresh(db_user)
            return {"code": 200, "url": file_path}
    except Exception as e:
        print(e)
        return {"code": 201, "message": e.args}
