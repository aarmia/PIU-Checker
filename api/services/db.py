import psycopg2
from psycopg2 import sql
from cachetools import TTLCache
from fastapi import HTTPException

# 캐시 설정 (30분 TTL, 최대 1000개)
image_cache = TTLCache(maxsize=1000, ttl=86400)

# 데이터베이스 연결 설정
def get_db_connection():
    return psycopg2.connect(
        dbname="piu_checker",   # your database name
        user="postgres",    # username
        password="1234",    # pw
        host="localhost",  # 또는 서버 IP
        port="5432"
    )

# 이미지 URL 조회
# DB에서 모든 곡 이미지 로드 (초기 캐싱)


def load_all_image_urls():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT song, image_url FROM song_images"
        cursor.execute(query)

        # 결과를 캐싱
        for song_id, image_url in cursor.fetchall():
            image_cache[song_id] = image_url
        print(f"캐싱 완료: {len(image_cache)} 개 항목 로드됨.")

        cursor.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 곡 이미지 URL 조회 (캐시 우선)
def get_image_url(song_id: str) -> str:
    if song_id in image_cache:
        return image_cache[song_id]
    try:
        # 2. 캐시에 없으면 DB 조회
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT image_url FROM song_images WHERE song_id = %s"
        cursor.execute(query, (song_id,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        # 3. 조회 성공 시 캐시에 추가
        if result:
            image_url = result[0]
            image_cache[song_id] = image_url  # 캐시 업데이트
            return image_url
        else:
            # 캐시에 없으면 기본 이미지 반환
            return "https://www.piugame.com/data/song_img/44b05993485fdf84f9503d7635461185.png"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 이미지 URL 추가 또는 업데이트
def upsert_image_url(song_name: str, image_url: str):
    """
    곡 이미지 URL 삽입 또는 업데이트
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO song_images (song, image_url)
        VALUES (%s, %s)
        ON CONFLICT (song) DO UPDATE
        SET image_url = EXCLUDED.image_url, created_at = NOW();
        """
        cursor.execute(query, (song_name, image_url))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
