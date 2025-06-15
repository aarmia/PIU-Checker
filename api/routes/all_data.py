from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from scraper import fetch_all_user_data
from api.services.limiter import rate_limiter

router = APIRouter(tags=["PIU - Checker"])

class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/fetch-all-user-data")
def fetch_all_user_data_endpoint(request: Request, credentials: UserCredentials):
    client_id = request.client.host
    limit_reset = rate_limiter(client_id, bucket="global")
    if limit_reset:
        raise HTTPException(
            status_code=429,
            detail={"message": "요청 제한 초과", "reset_time": str(limit_reset)}
        )

    try:
        data = fetch_all_user_data(credentials.username, credentials.password)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
