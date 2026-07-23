import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from app.config import get_settings

# In-memory sliding-window rate limiter (per API key).
# NOTE: for multi-instance deployment, replace with a Redis-backed limiter.
_request_log: dict[str, deque] = defaultdict(deque)


async def api_key_auth(request: Request):
    settings = get_settings()
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in settings.valid_api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

    now = time.time()
    window = _request_log[api_key]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    window.append(now)

    return api_key
