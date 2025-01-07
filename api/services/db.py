import psycopg2
from psycopg2 import sql
from fastapi import HTTPException

# 데이터베이스 연결 설정
def get_db_connection():
    return psycopg2.connect(
        dbname="piu_checker",
        user="postgres",
        password="1234",
        host="localhost",  # 또는 서버 IP
        port="5432"
    )

# 이미지 URL 조회
def get_image_url_from_db(song_name: str) -> str:
    """
    곡 이름으로 이미지 URL 조회
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = sql.SQL("SELECT image_url FROM song_images WHERE song = %s")
        cursor.execute(query, (song_name,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result[0]
        else:
            return "https://www.piugame.com/data/song_img/44b05993485fdf84f9503d7635461185.png"  # 기본 이미지 URL
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
