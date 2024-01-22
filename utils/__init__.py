# 生成随机token
import uuid


def generate_token():
    return str(uuid.uuid4()).replace("-", "")
