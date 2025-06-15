from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scraper import fetch_recently_played_data
from login import login_to_piugame

router = APIRouter()


# 현재는 사용하지 않는 엔드포인트: 사용을 위해서는 __init__.py 에 라우터를 등록해 주세요
class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/fetch-recently-played")
def fetch_recently_played_endpoint(credentials: UserCredentials):
    session = login_to_piugame(credentials.username, credentials.password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")

    url = "https://www.piugame.com/my_page/recently_played.php"
    response = session.get(url, verify=False, timeout=30)

    data = fetch_recently_played_data(response.text)
    return {"status": "success", "data": data}
