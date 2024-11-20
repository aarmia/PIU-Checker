import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# 사용자 로그인 데이터를 위한 모델
class UserCredentials(BaseModel):
    username: str
    password: str

# 로그인 및 세션 생성 함수
def login_to_piugame(username: str, password: str):
    login_url = "https://www.piugame.com/bbs/login_check.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.piugame.com/bbs/login.php",
        "Origin": "https://www.piugame.com"
    }

    session = requests.Session()

    try:
        # 로그인 페이지에서 CSRF 토큰 가져오기
        login_page = session.get("https://www.piugame.com/bbs/login.php", headers=headers, verify=False)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find("input", {"name": "csrf_token"})
        csrf_value = csrf_token["value"] if csrf_token else None

        # 로그인 요청 데이터
        login_payload = {
            "mb_id": username,
            "mb_password": password,
            "url": "/my_page/play_data.php"
        }

        if csrf_value:
            login_payload["csrf_token"] = csrf_value

        # 로그인 요청
        response = session.post(login_url, data=login_payload, headers=headers, verify=False, timeout=30)

        # 디버깅: 로그인 응답 HTML 저장
        with open("login_response_debug.html", "w", encoding="utf-8") as file:
            file.write(response.text)

        print("로그인 후 URL:", response.url)
        print("응답 코드:", response.status_code)
        print("쿠키 정보:", session.cookies)

        if "로그인 실패" in response.text or "login" in response.url:
            print("로그인 실패: 아이디 또는 비밀번호가 올바르지 않음")
            return None

        print("로그인 성공!")
        return session

    except requests.exceptions.Timeout:
        print("요청이 타임아웃되었습니다.")
        raise HTTPException(status_code=504, detail="요청 타임아웃")
    except requests.exceptions.RequestException as e:
        print(f"요청 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="로그인 요청 실패")

# HTML 데이터 파싱 함수
def parse_user_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 사용자 프로필 정보 추출
    user_data = {
        "level": soup.select_one(".subProfile_wrap .t1.en.col2").text.strip() if soup.select_one(".subProfile_wrap .t1.en.col2") else "Unknown",
        "nickname": soup.select_one(".subProfile_wrap .t2.en").text.strip() if soup.select_one(".subProfile_wrap .t2.en") else "Unknown",
        "last_login_date": (
            soup.find("li", text=lambda t: t and "최근 접속일" in t).text.split(":")[1].strip()
            if soup.find("li", text=lambda t: t and "최근 접속일" in t) else "Unknown"
        ),
        "last_play_location": (
            soup.find("li", text=lambda t: t and "최근 접속 게임장" in t).text.split(":")[1].strip()
            if soup.find("li", text=lambda t: t and "최근 접속 게임장" in t) else "Unknown"
        ),
        "points": soup.select_one(".profile_etc .tt.en").text.strip() if soup.select_one(".profile_etc .tt.en") else "0"
    }

    # 플레이 데이터 추출
    play_data = {
        "play_count": (
            soup.find("div", text="Play Count").find_next("i", class_="t2").text.strip()
            if soup.find("div", text="Play Count") else "0"
        ),
        "rating": soup.select_one(".play_data_wrap .num.fontSt").text.strip() if soup.select_one(".play_data_wrap .num.fontSt") else "0",
        "clear_data": soup.select_one(".clear_w .t1").text.strip() if soup.select_one(".clear_w .t1") else "0",
        "progress": (
            soup.select_one(".clear_w .graph .num").text.strip()
            if soup.select_one(".clear_w .graph .num") else "0%"
        )
    }

    return {"user_data": user_data, "play_data": play_data}

# FastAPI 엔드포인트
@app.post("/fetch-user-data")
def fetch_user_data(credentials: UserCredentials):
    try:
        # 로그인 및 세션 생성
        session = login_to_piugame(credentials.username, credentials.password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        # 보호된 페이지 요청
        protected_url = "https://www.piugame.com/my_page/play_data.php"
        response = session.get(protected_url, verify=False, timeout=30)

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
