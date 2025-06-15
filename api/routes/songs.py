import aiohttp
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from login import login_to_piugame
from scraper import fetch_song_details_for_all_levels, fetch_song_details_for_level
from api.services.db import get_image_url
from api.services.limiter import rate_limiter

router = APIRouter(tags=["PIU - Checker"])


class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/fetch-song-details")
async def fetch_song_details(request: Request, credentials: UserCredentials):
    client_id = request.client.host
    limit_reset = rate_limiter(client_id, bucket="global")
    if limit_reset:
        raise HTTPException(
            status_code=429,
            detail={"message": "요청 제한 초과", "reset_time": str(limit_reset)}
        )

    try:
        # 곡 데이터 수집
        song_data = await fetch_song_details_for_all_levels(credentials.username, credentials.password)

        # 이미지 URL 추가
        for level, data in song_data.items():
            for mode in ["single", "double"]:
                for song in data[mode]:
                    song_name = song["name"]
                    # DB에서 이미지 URL 조회 후 추가
                    song["image_url"] = get_image_url(song_name)

        return {"status": "success", "data": song_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-song-details/level/{level}")
async def fetch_song_details_by_level(
    level: int,
    request: Request,
    credentials: UserCredentials
):
    """
    지정된 레벨 단일 스크래핑
    """
    # 1) Rate limiting
    client_id = request.client.host
    limit_reset = rate_limiter(client_id, bucket="level")
    if limit_reset:
        raise HTTPException(
            status_code=429,
            detail={"message": "요청 제한 초과", "reset_time": str(limit_reset)}
        )

    # 2) 로그인 세션 생성
    session = login_to_piugame(credentials.username, credentials.password)

    # 3) 단일 레벨 스크래핑
    try:
        async with aiohttp.ClientSession(cookies=session.cookies.get_dict()) as async_session:
            # 진행률 트래커: 단일 레벨 1회 처리
            progress_tracker = {"completed": 0, "total": 1}
            song_list = await fetch_song_details_for_level(
                async_session,
                level,
                progress_tracker
            )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 4) 이미지 URL 보강
    from api.services.db import get_image_url
    for mode in ("single", "double"):
        for song in song_list.get(mode, []):
            song["image_url"] = get_image_url(song["name"])

    # 5) 응답 반환
    return {
        "status": "success",
        "level": level,
        "data": song_list
    }
