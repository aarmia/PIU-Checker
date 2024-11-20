from bs4 import BeautifulSoup

# 기존 사용자 데이터 스크래핑
def parse_user_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

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

# 새로 추가된 PUMBILITY 데이터 스크래핑
def parse_pumbility_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    main_pumbility = {
        "total_score": soup.select_one(".pumbility_total_wrap .t2.en").text.strip()
        if soup.select_one(".pumbility_total_wrap .t2.en") else "Unknown",
        "description": soup.select_one(".memo_wrap2.st3 .ti").text.strip()
        if soup.select_one(".memo_wrap2.st3 .ti") else "Unknown"
    }

    song_list = []
    song_items = soup.select(".pumbility_list .list > li")
    for song in song_items:
        song_data = {
            "song_name": song.select_one(".t1").text.strip() if song.select_one(".t1") else "Unknown",
            "artist": song.select_one(".t2").text.strip() if song.select_one(".t2") else "Unknown",
            "score": song.select_one(".score .tt.en").text.strip() if song.select_one(".score .tt.en") else "Unknown",
            "play_date": song.select_one(".date .tt").text.strip() if song.select_one(".date .tt") else "Unknown",
            "thumbnail_url": (
                song.select_one(".profile_img .re")["style"].split("url('")[1].split("')")[0]
                if song.select_one(".profile_img .re") and "url('" in song.select_one(".profile_img .re")["style"]
                else "Unknown"
            )
        }
        song_list.append(song_data)

    return {
        "main_pumbility": main_pumbility,
        "song_list": song_list
    }
