from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from login import login_to_piugame
from scraper import parse_user_data

router = APIRouter()

class UserCredentials(BaseModel):
    username: str
    password: str

@router.post("/fetch-user-data")
def fetch_user_data(credentials: UserCredentials, level: int = Query(None, title="레벨", description="특정 레벨 데이터를 가져옵니다.")):
    try:
        # 로그인 및 세션 생성
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        # 보호된 페이지 요청 URL
        base_url = "https://www.piugame.com/my_page/play_data.php"
        target_url = f"{base_url}?lv={level}" if level else base_url

        response = session.get(target_url, verify=False, timeout=30)

        # 디버깅: 응답 URL과 상태 코드 확인
        print("최종 URL:", response.url)
        print("응답 코드:", response.status_code)

        # 디버깅: HTML 내용을 파일로 저장
        with open("response_debug.html", "w", encoding="utf-8") as file:
            file.write(response.text)

        if response.status_code != 200 or "login" in response.url:
            raise HTTPException(status_code=500, detail="데이터 요청 실패: 로그인 상태 아님")

        # HTML 파싱 및 데이터 추출
        parsed_data = parse_user_data(response.text)

        return {"status": "success", "data": parsed_data}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"서버 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 에러: {str(e)}")
