from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from login import login_to_piugame

router = APIRouter()


# 현재는 사용하지 않는 엔드포인트: 사용을 위해서는 __init__.py 에 라우터를 등록해 주세요
class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(credentials: UserCredentials):
    session = login_to_piugame(credentials.username, credentials.password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")
    return {"status": "success", "message": "로그인 성공"}
