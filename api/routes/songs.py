from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from scraper import fetch_song_details_for_all_levels
from api.services.db import get_image_url
from api.services.limiter import rate_limiter

router = APIRouter()


class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/fetch-song-details")
async def fetch_song_details(request: Request, credentials: UserCredentials):
    client_id = request.client.host
    limit_reset = rate_limiter(client_id)
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
