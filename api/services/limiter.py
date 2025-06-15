from datetime import datetime, timedelta

# 1시간당 호출 허용 한도
LIMITS = {
    "global": 8,   # 기존 전체 스크래핑 등
    "level": 72,   # 레벨별 단일 스크래핑(18레벨 * 4회 여유)
}

# { client_id: { bucket_name: {"count": int, "reset_time": datetime} } }
user_request_log = {}


def rate_limiter(client_id: str, bucket: str = "global"):
    """
    client_id: 클라이언트 식별자(IP 등)
    bucket: 'global' 또는 'level'
    반환값: None      => 허용
          timedelta => 초과 시 남은 시간
    """
    now = datetime.now()
    # bucket 한도 가져오기
    limit = LIMITS.get(bucket, LIMITS["global"])

    # 클라이언트 로그 초기화
    if client_id not in user_request_log:
        user_request_log[client_id] = {}
    client_log = user_request_log[client_id]

    # 이 버킷의 기존 기록 가져오기
    entry = client_log.get(bucket)

    # 처음 요청이거나, 이전 윈도우가 만료되었을 경우
    if not entry or entry["reset_time"] <= now:
        client_log[bucket] = {
            "count": 1,
            "reset_time": now + timedelta(hours=1)
        }
        return None

    # 이미 한도를 초과했으면 남은 시간 반환
    if entry["count"] >= limit:
        return entry["reset_time"] - now

    # 아직 남아 있으면 카운트만 증가
    entry["count"] += 1
    return None
