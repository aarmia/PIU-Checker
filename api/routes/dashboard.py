from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.services.limiter import rate_limiter
from login import login_to_piugame
from bs4 import BeautifulSoup

router = APIRouter(tags=["Dashboard"])


class UserCredentials(BaseModel):
    username: str
    password: str


@router.post("/dashboard")
async def fetch_dashboard_data(
    request: Request,                    # Request 파라미터 추가
    credentials: UserCredentials
):
    # 1) Rate limiting (global 버킷)
    client_id = request.client.host
    reset = rate_limiter(client_id, bucket="global")
    if reset:
        # 남은 시간 reset(TimeDelta)을 반환하므로, 적절히 문자열화하여 응답
        raise HTTPException(
            status_code=429,
            detail={
                "message": "요청 제한 초과",
                "retry_after_seconds": int(reset.total_seconds())
            }
        )

    # 2) 로그인
    session = login_to_piugame(credentials.username, credentials.password)
    if not session:
        raise HTTPException(status_code=401, detail="로그인 실패")

    # 3) 랭킹 페이지 접근 및 데이터 추출
    rank_url = "https://www.piugame.com/leaderboard/pumbility_ranking.php"
    rank_html = session.get(rank_url, verify=False, timeout=30).text
    rank_soup = BeautifulSoup(rank_html, "html.parser")

    rank_box = rank_soup.select_one("ul.list.pumbilitySt2 li")
    id1 = rank_box.select_one(".profile_name.en.pl0").text.strip()
    id2 = rank_box.select_one(".profile_name.st1.en").text.strip()
    user_id = f"{id1} {id2}"

    ranking_raw = rank_box.select_one(".num .tt").text.strip()
    ranking = "1000+" if ranking_raw == "-" else ranking_raw

    score_str = rank_box.select_one(".score .tt.en").text.strip().replace(",", "")
    pumbility_score = int(score_str)
    bg_style = rank_box.select_one(".re.bgfix")["style"]
    img_url = bg_style.split("url('")[1].split("')")[0]

    info = {
        "id": user_id,
        "ranking": ranking,
        "img": img_url,
        "pumbility_score": pumbility_score
    }

    # 4) 펌빌리티 페이지에서 곡 리스트 추출
    pumbility_url = "https://www.piugame.com/my_page/pumbility.php"
    pumbility_html = session.get(pumbility_url, verify=False, timeout=30).text
    soup = BeautifulSoup(pumbility_html, "html.parser")
    full_song_list = []

    items = soup.select(".rating_rangking_list_w ul.list > li")
    for item in items:
        name = item.select_one(".name .t1").text.strip()
        score = item.select_one(".score .tt.en").text.strip()
        plate_img = item.select_one(".grade_wrap .img img")["src"]

        stepball_img_element = item.select_one(".stepBall_img_wrap .stepBall_in")
        step_type = "d" if "d_bg" in stepball_img_element["style"] else "s"

        stepball_inner_elements = item.select(".stepBall_img_wrap .stepBall_in .imG img")
        difficult = ''.join([
            img[-5] for img in [e["src"] for e in stepball_inner_elements if "src" in e.attrs]
            if img[-5].isdigit()
        ])

        bg_style = item.select_one(".profile_img .resize .re.bgfix")["style"]
        bg_url = bg_style.split("url('")[1].split("')")[0] if bg_style else None

        song = {
            "name": name,
            "score": score,
            "plate_img": plate_img,
            "bg_img": bg_url,
            "type": step_type,
            "difficult": difficult
        }
        full_song_list.append(song)

    top10 = full_song_list[:10]
    other40 = full_song_list[10:]

    # 5) 최종 응답
    return {
        "info": info,
        "TOP10": top10,
        "Other40": other40
    }
