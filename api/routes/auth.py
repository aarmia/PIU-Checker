from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from login import login_to_piugame

router = APIRouter()

class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(credentials: UserCredentials):
    session = login_to_piugame(credentials.username, credentials.password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")
    return {"status": "success", "message": "로그인 성공"}
