from bs4 import BeautifulSoup

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
