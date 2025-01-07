import asyncio
import aiohttp
import cachetools
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

    return user_data


def fetch_all_levels_data(session, base_url):
    """
    모든 레벨 데이터를 수집하여 반환. 'ALL' 데이터를 상단에 추가.
    """
    levels = list(range(10, 27)) + ["27over"]
    result_data = []  # 리스트로 데이터 저장
    plate_types = ["pg", "ug", "eg", "sg", "mg", "tg", "fg", "rg"]  # 8개 플레이트 정의

    # Step 1: Fetch "ALL" data from /fetch-user-data
    all_url = f"{base_url}"  # 중복 제거
    try:
        all_response = session.get(all_url, verify=False, timeout=30)
        all_response.raise_for_status()
        all_soup = BeautifulSoup(all_response.text, 'html.parser')

        # 플레이 데이터 추출
        rating = all_soup.select_one(".play_data_wrap .num.fontSt")
        clear_data = all_soup.select_one(".clear_w .t1")
        progress = all_soup.select_one(".clear_w .graph .num")

        progress_text = progress.text.strip() if progress else "0%"
        progress_percentage = progress_text.strip('%')
        progress_value = round(float(progress_percentage) / 100, 2) if progress_percentage.isdigit() else 0.0

        play_data = {
            "rating": rating.text.strip() if rating else "0",
            "clear_data": clear_data.text.strip() if clear_data else "0",
            "progress": progress_text,
            "progress_value": progress_value
        }

        # 플레이트 데이터 추출
        plate_data = {ptype: "0" for ptype in plate_types}
        plates = all_soup.select('.plate_w .list_in')
        for plate in plates:
            plate_type = plate.select_one('.play_log_btn[data-type]')
            if plate_type:
                plate_key = plate_type.get("data-type")
                if plate_key in plate_types:
                    plate_value = plate.select_one('.t_num').text.strip()
                    plate_data[plate_key] = plate_value

        result_data.append({
            "level": "ALL",
            "play_data": play_data,
            "plate_data": plate_data
        })
    except Exception as e:
        print(f"Error fetching ALL data: {e}")
        result_data.append({
            "level": "ALL",
            "play_data": {"rating": "0", "clear_data": "0/0", "progress": "0%", "progress_value": 0.0},
            "plate_data": {ptype: "0" for ptype in plate_types}
        })

    # Step 2: Fetch individual level data
    for level in levels:
        try:
            url = f"{base_url}?lv={level}" if level != "27over" else f"{base_url}?lv=27over"
            response = session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 플레이 데이터
            rating = soup.select_one(".play_data_wrap .num.fontSt")
            clear_data = soup.select_one(".clear_w .t1")
            progress = soup.select_one(".clear_w .graph .num")

            progress_text = progress.text.strip() if progress else "0%"
            progress_percentage = progress_text.strip('%')
            progress_value = round(float(progress_percentage) / 100, 2) if progress_percentage.isdigit() else 0.0

            play_data = {
                "rating": rating.text.strip() if rating else "0",
                "clear_data": clear_data.text.strip() if clear_data else "0",
                "progress": progress_text,
                "progress_value": progress_value
            }

            # 플레이트 데이터
            plate_data = {ptype: "0" for ptype in plate_types}
            plates = soup.select('.plate_w .list_in')
            for plate in plates:
                plate_type = plate.select_one('.play_log_btn[data-type]')
                if plate_type:
                    plate_key = plate_type.get("data-type")
                    if plate_key in plate_types:
                        plate_value = plate.select_one('.t_num').text.strip()
                        plate_data[plate_key] = plate_value

            result_data.append({
                "level": str(level),
                "play_data": play_data,
                "plate_data": plate_data
            })
        except Exception as e:
            print(f"Error processing level {level}: {e}")
            result_data.append({
                "level": str(level),
                "play_data": {"rating": "0", "clear_data": "0/0", "progress": "0%", "progress_value": 0.0},
                "plate_data": {ptype: "0" for ptype in plate_types}
            })

    return result_data


# 동시 요청 제한을 위한 Semaphore 설정
SEMAPHORE = asyncio.Semaphore(3)  # 최대 3개의 요청만 동시 처리

# TTL 캐시 설정 (최대 100개, 300초 유지)
cache = cachetools.TTLCache(maxsize=100, ttl=300)

# 데이터베이스 설정
DB_CONFIG = {
    "dbname": "piu_checker",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}
async def fetch_page_with_retry(session, url, retries=3):
    """
    재시도 기능이 포함된 페이지 데이터 요청 함수.
    """
    for attempt in range(retries):
        try:
            async with SEMAPHORE:  # 동시 요청 제한 적용
                async with session.get(url, timeout=60) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            print(f"[ERROR] 요청 실패 (재시도 {attempt + 1}/{retries}): {str(e)}")
            if attempt == retries - 1:  # 마지막 재시도 실패 시 예외 처리
                raise HTTPException(status_code=500, detail=f"최종 요청 실패: {str(e)}")
            await asyncio.sleep(2)  # 재시도 대기 시간 (2초)


async def fetch_song_details_for_level(session, level, progress_tracker):
    """
    특정 레벨의 곡 데이터를 수집합니다.
    """

    # 캐시 확인
    if level in cache:
        print(f"[INFO] Level {level} 캐시에서 데이터 반환")
        return cache[level]

    base_url = "https://www.piugame.com/my_page/my_best_score.php"
    song_data = {"single": [], "double": []}
    page = 1

    while True:
        try:
            url = f"{base_url}?lv={level}&page={page}"
            html = await fetch_page_with_retry(session, url)  # 동시 요청 제한 / 재시도 기능 적용
            soup = BeautifulSoup(html, "html.parser")

            # 곡 데이터 추출
            song_items = soup.select(".my_best_scoreList li")
            if not song_items:
                break

            for song in song_items:
                # 곡 이름
                name_element = song.select_one(".song_name p")
                if not name_element:
                    continue
                song_name = name_element.text.strip()

                # 점수
                score_element = song.select_one(".txt_v .num")
                score = int(score_element.text.replace(",", "")) if score_element else 0

                # NN.N 형식으로 변환
                formatted_score = round(score / 10000, 1)

                # 싱글/더블 구분
                type_element = song.select_one(".stepBall_img_wrap .tw img")
                song_type = "double" if "d_text" in type_element.get("src", "") else "single"

                # 데이터 추가
                song_data[song_type].append({
                    "name": song_name,
                    "score": formatted_score
                })

            # 다음 페이지 확인
            current_page = int(soup.select_one(".board_paging .on").text.strip())
            max_page = max(int(btn.text.strip()) for btn in soup.select(".board_paging button:not(.icon)"))
            if current_page >= max_page:
                break
            page += 1

        except Exception as e:
            print(f"레벨 {level}, 페이지 {page} 처리 중 오류 발생: {e}")
            break

    # 점수 기준 내림차순 정렬
    song_data["single"].sort(key=lambda x: float(x["score"]), reverse=True)
    song_data["double"].sort(key=lambda x: float(x["score"]), reverse=True)

    # 진행 상황 메시지 추가
    progress_tracker["completed"] += 1
    print(f"[INFO] Level {level} 완료. 진행률: {progress_tracker['completed']}/{progress_tracker['total']}")

    # 캐시 저장
    cache[level] = song_data
    return song_data


async def fetch_song_details_for_all_levels(username, password):
    """
    모든 레벨의 곡 데이터를 병렬 처리 및 동시 요청 제한을 적용하여 수집합니다.
    """
    # 로그인 세션 생성
    session = login_to_piugame(username, password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")

    # 요청할 레벨 목록
    levels = list(range(10, 28))  # 10~27레벨

    # 진행 상황 추적기 설정
    progress_tracker = {"total": len(levels), "completed": 0}

    # 병렬 요청 수행
    async with aiohttp.ClientSession(cookies=session.cookies) as async_session:
        tasks = [fetch_song_details_for_level(async_session, level, progress_tracker) for level in levels]
        results = await asyncio.gather(*tasks)

    # 레벨별 결과 매핑
    return {f"level_{level}": data for level, data in zip(levels, results)}


def extract_pumbility_score_and_songs(html_content):
    """
    Pumbility 점수와 곡 리스트에서 Plate 정보를 포함해 데이터를 반환.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Pumbility 점수 추출
    score_tag = soup.select_one('.pumbility_total_wrap .t2.en')
    pumbility_score_element = score_tag.text.strip() if score_tag else "Unknown"

    # "," 제거 및 정수 변환
    pumbility_score = int(pumbility_score_element.replace(",", ""))

    # 곡 리스트 추출
    song_list = []
    song_items = soup.select('.rating_rangking_list_w ul.list > li')

    for item in song_items:
        # 곡 이름
        name_tag = item.select_one('.name .t1')

        # 아티스트
        artist_tag = item.select_one('.name .t2')

        # 펌빌리티 점수
        score_tag = item.select_one('.score .tt.en')

        # 날짜
        date_tag = item.select_one('.date .tt')

        # 플레이트 이미지 URL
        plate_img_element = item.select_one(".grade_wrap .img img")
        plate_img = plate_img_element["src"] if plate_img_element else "Unknown"

        # 스텝볼 이미지 URL
        stepball_img_element = item.select_one(".stepBall_img_wrap .stepBall_in")
        stepball_img = stepball_img_element["style"].split("url(")[-1].strip(")") if stepball_img_element else "Unknown"

        # 스텝볼 타입 결정 (d 또는 s)
        step_type = "d" if "d_bg" in stepball_img else "s"

        # 스텝볼 내부 `tw` div 클래스의 이미지 URL
        stepball_tw_element = item.select_one(".stepBall_img_wrap .stepBall_in .tw img")
        stepball_tw_img = stepball_tw_element["src"] if stepball_tw_element else "Unknown"

        # 스텝볼 내부 하위 이미지 URL
        stepball_inner_elements = item.select(".stepBall_img_wrap .stepBall_in .imG img")
        stepball_inner_images = [
            img["src"] for img in stepball_inner_elements if "src" in img.attrs
        ]

        # 배경 이미지 URL
        bg_style = item.select_one('.profile_img .resize .re.bgfix')['style']
        bg_url = bg_style.split("url('")[1].split("')")[0] if bg_style else None

        song_data = {
            "name": name_tag.text.strip() if name_tag else "Unknown",
            "artist": artist_tag.text.strip() if artist_tag else "Unknown",
            "score": score_tag.text.strip() if score_tag else "Unknown",
            "date": date_tag.text.strip() if date_tag else "Unknown",
            "plate_img": plate_img,
            "step_type": step_type,
            "stepball_tw_img": stepball_tw_img,
            "stepball_inner_img": stepball_inner_images,
            "bg_img": bg_url,
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

            # .li_in.ac 이미지 URL 추출
            plate_tag = item.select_one('.li_in.ac img')
            plate_url = plate_tag["src"] if plate_tag and plate_tag.get("src") else "0"

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
            "pumbility_data": pumbility_data,
            "recently_played_data": recently_played_data,
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
