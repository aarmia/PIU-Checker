import aiohttp
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from login import login_to_piugame
from scraper import fetch_song_details_for_all_levels, fetch_song_details_for_level
from api.services.db import get_image_url, get_full_song_list  # ← get_full_song_list 추가
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
        # 전체 레벨 스크래핑
        song_data = await fetch_song_details_for_all_levels(
            credentials.username, credentials.password
        )

        # 이미지 URL 보강
        for level, data in song_data.items():
            for mode in ["single", "double"]:
                for song in data[mode]:
                    song_name = song["name"]
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
    지정된 레벨 단일 스크래핑 + 미클리어 포함 + 모드별 clear/total 카운트
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

    # 3) 단일 레벨 스크래핑 (cleared_data: {"single":[], "double":[]})
    try:
        async with aiohttp.ClientSession(cookies=session.cookies.get_dict()) as async_sess:
            progress_tracker = {"completed": 0, "total": 1}
            cleared_data = await fetch_song_details_for_level(
                async_sess, level, progress_tracker
            )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 4) 전체 곡 리스트 조회 (DB)
    #    {"single":[(name,img_url),...], "double":[...]}
    full_list = get_full_song_list(level)

    # 5) 모드별 clear/total 카운트 계산
    single_clear = len(cleared_data.get("single", []))
    single_total = len(full_list.get("single", []))
    double_clear = len(cleared_data.get("double", []))
    double_total = len(full_list.get("double", []))

    # 6) cleared_data 리스트에 미클리어 항목 추가
    for mode in ("single", "double"):
        cleared_names = {s["name"] for s in cleared_data.get(mode, [])}
        for name, img_url in full_list.get(mode, []):
            if name not in cleared_names:
                cleared_data[mode].append({
                    "name": name,
                    "score": None,  # 미클리어는 score None
                    "img_url": img_url
                })

    # 7) 클리어된 곡에도 image_url 보강 (이미지 매핑)
    for mode in ("single", "double"):
        for song in cleared_data.get(mode, []):
            # 이미 img_url 필드가 있으므로, DB 매핑은 클리어된 곡만
            if song.get("score") is not None:
                song["image_url"] = get_image_url(song["name"])

    # 8) 최종 응답 반환
    return {
        "status": "success",
        "level": level,
        "single_clear": single_clear,
        "single_total": single_total,
        "double_clear": double_clear,
        "double_total": double_total,
        "data": cleared_data
    }
