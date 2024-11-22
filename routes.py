from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from login import login_to_piugame
from scraper import parse_user_data, extract_pumbility_score_and_songs, fetch_all_levels_data

router = APIRouter()

class UserCredentials(BaseModel):
    username: str
    password: str

@router.post("/fetch-user-data")
def fetch_user_data(credentials: UserCredentials):
    """
    사용자 데이터를 가져오는 엔드포인트
    """
    try:
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        target_url = "https://www.piugame.com/my_page/play_data.php"
        response = session.get(target_url, verify=False, timeout=30)

        parsed_data = parse_user_data(response.text)
        return {"status": "success", "data": parsed_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-all-levels-data")
def fetch_all_levels_data_endpoint(credentials: UserCredentials):
    """
    모든 레벨 데이터를 수집하여 반환하는 엔드포인트
    """
    try:
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        base_url = "https://www.piugame.com/my_page/play_data.php"
        all_levels_data = fetch_all_levels_data(session, base_url)

        return {"status": "success", "data": all_levels_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-pumbility-data")
def fetch_pumbility_data(credentials: UserCredentials):
    """
    Pumbility 데이터를 가져오는 엔드포인트
    """
    try:
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        pumbility_url = "https://www.piugame.com/my_page/pumbility.php"
        response = session.get(pumbility_url, verify=False, timeout=30)

        parsed_data = extract_pumbility_score_and_songs(response.text)
        return {"status": "success", "data": parsed_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
