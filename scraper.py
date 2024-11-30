import time

import requests
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
        "level": soup.select_one(".subProfile_wrap .t1.en").text.strip()
        if soup.select_one(".subProfile_wrap .t1.en") else "Unknown",
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


def fetch_all_levels_data(session, base_url):
    """
    모든 레벨(10~27over)의 데이터를 수집하여 반환
    """
    levels = list(range(10, 27)) + ["27over"]
    level_data = {}

    for level in levels:
        # URL 생성
        url = f"{base_url}?lv={level}" if level != "27over" else f"{base_url}?lv=27over"

        # 레벨별 페이지 요청
        response = session.get(url, verify=False, timeout=30)
        response.raise_for_status()

        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 데이터 추출
        rating = soup.select_one(".play_data_wrap .num.fontSt")
        clear_data = soup.select_one(".clear_w .t1")

        # 레벨 데이터 저장
        level_data[level] = {
            "rating": rating.text.strip() if rating else "0",
            "clear_data": clear_data.text.strip() if clear_data else "0"
        }

    return level_data


def fetch_song_details_for_level(session: requests.Session, level: int):
    base_url = "https://www.piugame.com/my_page/my_best_score.php"
    song_data = {"single": [], "double": []}
    page = 1

    while True:
        print(f"Fetching page {page} for level {level}...")
        url = f"{base_url}?lv={level}&&page={page}"
        response = session.get(url, verify=False, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 곡 정보를 포함하는 리스트 선택
        song_items = soup.select(".my_best_scoreList li")
        if not song_items:
            break  # 더 이상 곡 정보가 없으면 종료

        for index, song in enumerate(song_items):
            try:
                # 곡 이름 확인
                name_element = song.select_one(".song_name p")
                if not name_element:
                    continue
                song_name = name_element.text.strip()

                # 점수 확인
                score_element = song.select_one(".txt_v .num")
                if not score_element:
                    print(f"Skipping item {index}: score not found")
                    continue
                score_text = score_element.text.strip().replace(",", "")
                score = int(score_text)
                formatted_score = (
                    f"{score / 10000:.1f}" if score < 1000000 else f"{score // 10000}"
                )

                # 스코어가 0인 경우 생략
                if formatted_score == "0.0":
                    print(f"Skipping item {index}: score is 0")
                    continue

                # 곡 타입 확인
                type_element = song.select_one(".stepBall_img_wrap .tw img")
                if not type_element:
                    print(f"Skipping item {index}: type information not found")
                    continue
                type_url = type_element.get("src", "")
                song_type = "double" if "d_text" in type_url else "single"

                # 결과 저장
                song_data[song_type].append(
                    {
                        "name": song_name,
                        "score": float(formatted_score),
                    }
                )

            except Exception as e:
                print(f"Error parsing song item at index {index}: {e}")

        next_page = soup.select_one(".board_paging .xi.next")
        if not next_page:
            print("No more items found")
            break

        page += 1
        time.sleep(1)

    # 점수 기준 내림차순 정렬
    song_data["single"].sort(key=lambda x: x["score"], reverse=True)
    song_data["double"].sort(key=lambda x: x["score"], reverse=True)

    return song_data



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


def fetch_recently_played_data(html_content):
    """
    최근 플레이한 기록 데이터를 HTML에서 스크래핑하여 반환
    """
    soup = BeautifulSoup(html_content, "html.parser")
    songs = []

    song_items = soup.select(".recently_playeList > li")
    for item in song_items:
        try:
            # 곡 제목
            song_name = item.select_one(".song_name p").text.strip()

            # 플레이 스코어
            score_element = item.select_one(".li_in.ac .tx")
            score = score_element.text.strip() if score_element else "0"

            # 난이도
            level_imgs = item.select(".stepBall_in .numw .imG img")
            difficulty = "".join(
                [img["alt"].replace("d_num_", "").replace(".png", "") for img in level_imgs]
            )

            # 곡 타입
            type_img = item.select_one(".stepBall_in .tw img")
            song_type = "double" if "d_text" in type_img["src"] else "single"

            # 판정 정보
            judgement_table = item.select(".board_st.ac.recently_play tbody tr td .tx")
            judgement_info = {
                "perfect": judgement_table[0].text.strip() if len(judgement_table) > 0 else "0",
                "great": judgement_table[1].text.strip() if len(judgement_table) > 1 else "0",
                "good": judgement_table[2].text.strip() if len(judgement_table) > 2 else "0",
                "bad": judgement_table[3].text.strip() if len(judgement_table) > 3 else "0",
                "miss": judgement_table[4].text.strip() if len(judgement_table) > 4 else "0",
            }

            # 플레이트 이미지 URL
            plate_img = item.select_one(".li_in.st1 img")
            plate_url = plate_img["src"] if plate_img else "STAGE BREAK"

            # 곡 배경 URL
            background_style = item.select_one(".wrap_in .in.bgfix")["style"]
            background_url = background_style.split("url('")[1].split("')")[0]

            # 데이터 추가
            songs.append({
                "song_name": song_name,
                "score": score,
                "difficulty": difficulty,
                "type": song_type,
                "judgement": judgement_info,
                "plate_url": plate_url,
                "background_url": background_url,
            })
        except Exception as e:
            print(f"Error parsing song item: {e}")

    return songs

