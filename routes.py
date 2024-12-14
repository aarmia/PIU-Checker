from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from login import login_to_piugame
from scraper import (
    parse_user_data,
    extract_pumbility_score_and_songs,
    fetch_all_levels_data,
    fetch_recently_played_data,
    fetch_all_user_data, fetch_song_details_for_all_levels,
)

# 라우터 초기화
router = APIRouter()


RATE_LIMIT = 5
user_request_log ={}
class UserCredentials(BaseModel):
    username: str
    password: str


def rate_limiter(client_id: str):
    """
    Rate Limiting: 사용자 요청 제한 및 남은 시간 계산
    """
    now = datetime.now()
    if client_id not in user_request_log:
        user_request_log[client_id] = {"count": 1, "reset_time": now + timedelta(hours=1)}
        return None  # 제한 없음

    log = user_request_log[client_id]
    if log["reset_time"] < now:
        # 제한 시간 초기화
        user_request_log[client_id] = {"count": 1, "reset_time": now + timedelta(hours=1)}
        return None

    if log["count"] >= RATE_LIMIT:
        # 요청 제한 초과
        remaining_time = log["reset_time"] - now
        return remaining_time

    # 요청 수 증가
    log["count"] += 1
    return None


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

        # user_data, play_data, plate_data 파싱
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


@router.post("/fetch-song-details")
async def fetch_song_details(credentials: UserCredentials):
    """
    모든 레벨(10~27)의 곡 정보를 가져오는 엔드포인트 / 따로 사용
    """
    try:
        song_data = await fetch_song_details_for_all_levels(credentials.username, credentials.password)
        return {"status": "success", "data": song_data}
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


@router.post("/fetch-recently-played")
def fetch_recently_played_endpoint(credentials: UserCredentials):
    """
    최근 플레이한 기록 데이터를 가져오는 엔드포인트
    """
    try:
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        recently_played_url = "https://www.piugame.com/my_page/recently_played.php"
        response = session.get(recently_played_url, verify=False, timeout=30)

        data = fetch_recently_played_data(response.text)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-all-user-data")
def fetch_all_user_data_endpoint(request: Request, credentials: UserCredentials):
    """
    모든 데이터를 한 번의 요청으로 가져오는 엔드포인트
    """
    client_id = request.client.host  # 클라이언트의 IP 기반 식별
    limit_reset = rate_limiter(client_id)
    if limit_reset:
        return JSONResponse(
            status_code=429,  # Too Many Requests
            content={
                "status": "error",
                "message": f"요청 제한 초과: {RATE_LIMIT}회 요청 허용",
                "reset_time": str(limit_reset),
            },
        )

    try:
        data = fetch_all_user_data(credentials.username, credentials.password)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
