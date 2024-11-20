from bs4 import BeautifulSoup
import requests


def fetch_page_content(url, cookies=None):
    response = requests.get(url, cookies=cookies, verify=False, timeout=30)
    response.raise_for_status()
    return response.text


def parse_user_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    user_data = {
        "level": soup.select_one(".subProfile_wrap .t1.en.col2").text.strip()
        if soup.select_one(".subProfile_wrap .t1.en.col2") else "Unknown",
        "nickname": soup.select_one(".subProfile_wrap .t2.en").text.strip()
        if soup.select_one(".subProfile_wrap .t2.en") else "Unknown",
        "last_login_date": (
            soup.find("li", text=lambda t: t and "최근 접속일" in t).text.split(":")[1].strip()
            if soup.find("li", text=lambda t: t and "최근 접속일" in t) else "Unknown"
        ),
        "last_play_location": (
            soup.find("li", text=lambda t: t and "최근 접속 게임장" in t).text.split(":")[1].strip()
            if soup.find("li", text=lambda t: t and "최근 접속 게임장" in t) else "Unknown"
        ),
        "points": soup.select_one(".profile_etc .tt.en").text.strip()
        if soup.select_one(".profile_etc .tt.en") else "0"
    }

    play_data = {
        "play_count": (
            soup.find("div", text="Play Count").find_next("i", class_="t2").text.strip()
            if soup.find("div", text="Play Count") else "0"
        ),
        "rating": soup.select_one(".play_data_wrap .num.fontSt").text.strip()
        if soup.select_one(".play_data_wrap .num.fontSt") else "0",
        "clear_data": soup.select_one(".clear_w .t1").text.strip()
        if soup.select_one(".clear_w .t1") else "0",
        "progress": (
            soup.select_one(".clear_w .graph .num").text.strip()
            if soup.select_one(".clear_w .graph .num") else "0%"
        )
    }

    return {"user_data": user_data, "play_data": play_data}


def extract_pumbility_score_and_songs(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    score_tag = soup.select_one('.pumbility_total_wrap .t2.en')
    pumbility_score = score_tag.text.strip() if score_tag else "Unknown"

    song_list = []
    song_items = soup.select('.rating_rangking_list_w ul.list > li')
    for item in song_items:
        name_tag = item.select_one('.name .t1')
        artist_tag = item.select_one('.name .t2')
        score_tag = item.select_one('.score .tt.en')
        date_tag = item.select_one('.date .tt')

        song_data = {
            "name": name_tag.text.strip() if name_tag else "Unknown",
            "artist": artist_tag.text.strip() if artist_tag else "Unknown",
            "score": score_tag.text.strip() if score_tag else "Unknown",
            "date": date_tag.text.strip() if date_tag else "Unknown"
        }
        song_list.append(song_data)

    return {
        "pumbility_score": pumbility_score,
        "song_list": song_list
    }
