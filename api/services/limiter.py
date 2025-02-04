from datetime import datetime, timedelta

RATE_LIMIT = 8
user_request_log = {}


def rate_limiter(client_id: str):
    now = datetime.now()
    if client_id not in user_request_log:
        user_request_log[client_id] = {"count": 1, "reset_time": now + timedelta(hours=1)}
        return None

    log = user_request_log[client_id]
    if log["reset_time"] < now:
        user_request_log[client_id] = {"count": 1, "reset_time": now + timedelta(hours=1)}
        return None

    if log["count"] >= RATE_LIMIT:
        remaining_time = log["reset_time"] - now
        return remaining_time

    log["count"] += 1
    return None
