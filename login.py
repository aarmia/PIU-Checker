import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

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
