from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scraper import extract_pumbility_score_and_songs
from login import login_to_piugame

router = APIRouter()

class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/fetch-pumbility-data")
def fetch_pumbility_data(credentials: UserCredentials):
    session = login_to_piugame(credentials.username, credentials.password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")

    url = "https://www.piugame.com/my_page/pumbility.php"
    response = session.get(url, verify=False, timeout=30)

    parsed_data = extract_pumbility_score_and_songs(response.text)
    return {"status": "success", "data": parsed_data}
