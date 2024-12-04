import time
import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

from login import login_to_piugame


def fetch_page_content(url, cookies=None):
    """
    페이지의 HTML 콘텐츠를 가져오는 함수
    """
    import requests
    response = requests.get(url, cookies=cookies, verify=False, timeout=30)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return response.text


def parse_user_data(html_content):
    """
    사용자 데이터와 플레이 데이터를 HTML에서 파싱하여 반환
    """
    soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')

    # user_data 추출
    profile_img_style = soup.select_one('.profile_img .bgfix')["style"]
    profile_img = (
        profile_img_style.split("url('")[1].split("')")[0]
        if "url('" in profile_img_style else "Unknown"
    )

    play_count_element = soup.select_one('.board_search .total .t2')
    play_count = play_count_element.text.strip() if play_count_element else "0"

    user_data = {
        "level": soup.select_one(".subProfile_wrap .t1.en").text.strip()
        if soup.select_one(".subProfile_wrap .t1.en") else "Unknown",
        "nickname": soup.select_one(".subProfile_wrap .t2.en").text.strip()
        if soup.select_one(".subProfile_wrap .t2.en") else "Unknown",
        "profile_img": profile_img,
        "play_count": play_count
    }

    # play_data 추출
    rating_element = soup.select_one(".play_data_wrap .num.fontSt")
    clear_data_element = soup.select_one(".clear_w .t1")
    progress_element = soup.select_one(".clear_w .graph .num")

    play_data = {
        "rating": rating_element.text.strip() if rating_element else "0",
        "clear_data": clear_data_element.text.strip() if clear_data_element else "0",
        "progress": progress_element.text.strip() if progress_element else "0%"
    }

    # plate_data 추출
    plate_data = {}
    plate_items = soup.select('.plate_w .list_in')
    for plate in plate_items:
        plate_type = plate.select_one('.play_log_btn[data-type]')["data-type"]
        plate_value = plate.select_one('.t_num').text.strip()
        plate_data[plate_type] = plate_value

    return {"user_data": user_data, "play_data": play_data, "plate_data": plate_data}



def fetch_all_levels_data(session, base_url):
    """
    모든 레벨 데이터를 수집하여 반환, plate_data 포함
    """
    levels = list(range(10, 27)) + ["27over"]
    level_data = {}
    plate_types = ["pg", "ug", "eg", "sg", "mg", "tg", "fg", "rg"]  # 8개 플레이트 정의

    for level in levels:
        try:
            # URL 생성
            url = f"{base_url}?lv={level}" if level != "27over" else f"{base_url}?lv=27over"

            # 레벨별 페이지 요청
            response = session.get(url, verify=False, timeout=30)
            response.encoding = 'utf-8'
            response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 플레이 데이터 추출
            rating_element = soup.select_one(".play_data_wrap .num.fontSt")
            clear_data_element = soup.select_one(".clear_w .t1")
            progress_element = soup.select_one(".clear_w .graph .num")

            play_data = {
                "rating": rating_element.text.strip() if rating_element else "0",
                "clear_data": clear_data_element.text.strip() if clear_data_element else "0",
                "progress": progress_element.text.strip() if progress_element else "0%"
            }

            # Plate 데이터 추출
            plate_data = {ptype: "0" for ptype in plate_types}  # 기본값 설정
            plate_items = soup.select('.plate_w .list_in')
            for plate in plate_items:
                play_log_btn = plate.select_one('.play_log_btn[data-type]')
                if play_log_btn:
                    plate_type = play_log_btn.get("data-type")
                    if plate_type in plate_types:
                        plate_value_element = plate.select_one('.t_num')
                        plate_value = plate_value_element.text.strip() if plate_value_element else "0"
                        plate_data[plate_type] = plate_value

            # 레벨 데이터 저장
            level_data[level] = {
                "play_data": play_data,
                "plate_data": plate_data
            }

        except Exception as e:
            # 디버깅 로그 추가
            print(f"Error processing level {level}: {e}")
            level_data[level] = {
                "play_data": {"rating": "0", "clear_data": "0", "progress": "0%"},
                "plate_data": {ptype: "0" for ptype in plate_types}
            }

    return level_data


def fetch_song_details_for_level(session: requests.Session, level: int):
    base_url = "https://www.piugame.com/my_page/my_best_score.php"
    song_data = {"single": [], "double": []}
    page = 1

    while True:
        print(f"Fetching page {page} for level {level}...")
        url = f"{base_url}?lv={level}&&page={page}"
        response = session.get(url, verify=False, timeout=90)
        response.encoding = 'utf-8'
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

            # stepball 관련 이미지 소스 가져오기
            stepball_div = item.select_one(".stepBall_in")
            stepball_url = stepball_div["style"].split("url('")[1].split("')")[0]
            stepball_text = stepball_div.select_one(".tw img")["src"]
            stepball_num_imgs = stepball_div.select(".numw .imG img")
            stepball_num1 = stepball_num_imgs[0]["src"] if len(stepball_num_imgs) > 0 else None
            stepball_num2 = stepball_num_imgs[1]["src"] if len(stepball_num_imgs) > 1 else None

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
                "stepball_url": stepball_url,
                "stepball_text": stepball_text,
                "stepball_num1": stepball_num1,
                "stepball_num2": stepball_num2,
                "judgement": judgement_info,
                "plate_url": plate_url,
                "background_url": background_url,
            })
        except Exception as e:
            print(f"Error parsing song item: {e}")

    return songs


def fetch_all_user_data(username: str, password: str):
    """
    사용자 계정을 통해 모든 데이터를 한 번에 가져오는 함수
    """
    try:
        session = login_to_piugame(username, password)

        if not session:
            raise HTTPException(status_code=401, detail="로그인 실패")

        # 사용자 기본 데이터
        target_url = "https://www.piugame.com/my_page/play_data.php"
        response = session.get(target_url, verify=False, timeout=30)
        response.encoding = 'utf-8'
        user_data = parse_user_data(response.text)



        # 모든 레벨 데이터
        base_url = "https://www.piugame.com/my_page/play_data.php"
        all_levels_data = fetch_all_levels_data(session, base_url)

        # 특정 레벨별 곡 데이터 (10~27)
        song_details = {}
        for level in range(10, 28):
            try:
                song_details[level] = fetch_song_details_for_level(session, level)
            except Exception:
                song_details[level] = {"message": f"Level {level} 데이터 없음"}

        # Pumbility 데이터
        pumbility_url = "https://www.piugame.com/my_page/pumbility.php"
        response = session.get(pumbility_url, verify=False, timeout=30)
        pumbility_data = extract_pumbility_score_and_songs(response.text)

        # 최근 플레이 기록 데이터
        recently_played_url = "https://www.piugame.com/my_page/recently_played.php"
        response = session.get(recently_played_url, verify=False, timeout=30)
        recently_played_data = fetch_recently_played_data(response.text)

        # 결과 병합
        result = {
            "user_data": user_data,
            "all_levels_data": all_levels_data,
            "song_details": song_details,
            "pumbility_data": pumbility_data,
            "recently_played_data": recently_played_data,
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
