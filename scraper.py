import re
from bs4 import BeautifulSoup

def fetch_page_content(url, cookies=None):
    """
    페이지의 HTML 콘텐츠를 가져오는 함수
    """
    import requests
    response = requests.get(url, cookies=cookies, verify=False, timeout=30)
    response.raise_for_status()
    return response.text


def parse_user_data(html_content):
    """
    사용자 데이터를 HTML에서 파싱하여 반환
    """
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


def extract_plate_grade(item):
    """
    Plate 정보를 추출하고, 등급 정보를 반환.
    """
    plate_tag = item.select_one('.grade_wrap .img img')  # Plate 이미지 선택
    if not plate_tag or "src" not in plate_tag.attrs:
        return "Unknown"

    image_url = plate_tag["src"]
    # URL에서 파일명 추출
    image_filename = image_url.split("/")[-1]  # 예: "aa_p.png"

    # Plate 정보 처리
    if "_p" in image_filename:
        grade = image_filename.replace("_p", "").replace(".png", "").upper()
        """
        print(f"DEBUG: Plate 파일명 - {image_filename}, 결과 - {grade}")
        """
        return f"{grade}+"
    else:
        grade = image_filename.replace(".png", "").upper()
        return grade





def extract_pumbility_score_and_songs(html_content):
    """
    Pumbility 점수와 곡 리스트에서 Plate 정보를 포함해 데이터를 반환.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Pumbility 점수 추출
    score_tag = soup.select_one('.pumbility_total_wrap .t2.en')
    pumbility_score = score_tag.text.strip() if score_tag else "Unknown"

    # 곡 리스트 추출
    song_list = []
    song_items = soup.select('.rating_rangking_list_w ul.list > li')
    for item in song_items:
        name_tag = item.select_one('.name .t1')
        artist_tag = item.select_one('.name .t2')
        score_tag = item.select_one('.score .tt.en')
        date_tag = item.select_one('.date .tt')

        # Plate 등급 정보 추출
        plate_grade = extract_plate_grade(item)

        song_data = {
            "name": name_tag.text.strip() if name_tag else "Unknown",
            "artist": artist_tag.text.strip() if artist_tag else "Unknown",
            "score": score_tag.text.strip() if score_tag else "Unknown",
            "date": date_tag.text.strip() if date_tag else "Unknown",
            "plate": plate_grade  # Plate 등급 정보
        }
        song_list.append(song_data)

    return {
        "pumbility_score": pumbility_score,
        "song_list": song_list
    }
