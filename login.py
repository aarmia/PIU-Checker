import requests
import urllib3
from bs4 import BeautifulSoup
from fastapi import HTTPException

# HTTPS 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def login_to_piugame(username: str, password: str):
    login_url = "https://www.piugame.com/bbs/login_check.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.piugame.com/bbs/login.php",
        "Origin": "https://www.piugame.com"
    }

    session = requests.Session()

    try:
        # CSRF 토큰 추출
        login_page = session.get("https://www.piugame.com/bbs/login.php", headers=headers, verify=False)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find("input", {"name": "csrf_token"})
        csrf_value = csrf_token["value"] if csrf_token else None

        # 로그인 요청 데이터 구성
        login_payload = {
            "mb_id": username,
            "mb_password": password,
            "url": "/my_page/play_data.php"
        }

        if csrf_value:
            login_payload["csrf_token"] = csrf_value

        # 로그인 요청
        response = session.post(login_url, data=login_payload, headers=headers, verify=False, timeout=30)

        # 로그인 실패 처리
        if "로그인 실패" in response.text or "login" in response.url:
            raise HTTPException(status_code=401, detail="로그인 실패")

        print("로그인 성공")
        return session

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"로그인 실패: {str(e)}")
