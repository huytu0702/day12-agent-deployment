"""Redis-backed sliding-window rate limiter."""

from __future__ import annotations

import time
import uuid

from fastapi import HTTPException


RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now_ms - window_ms)
local count = redis.call('ZCARD', key)
if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry_after = 1
  if oldest[2] then
    retry_after = math.max(1, math.ceil((tonumber(oldest[2]) + window_ms - now_ms) / 1000))
  end
  return {0, count, retry_after}
end

redis.call('ZADD', key, now_ms, member)
redis.call('PEXPIRE', key, window_ms + 1000)
return {1, count + 1, 0}
"""


class RedisRateLimiter:
    def __init__(self, redis_client, max_requests: int, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(self, user_id: str) -> dict[str, int]:
        now_ms = int(time.time() * 1000)
        result = await self.redis.eval(
            RATE_LIMIT_SCRIPT,
            1,
            f"rate_limit:{user_id}",
            now_ms,
            self.window_seconds * 1000,
            self.max_requests,
            str(uuid.uuid4()),
        )

        allowed = int(result[0]) == 1
        count = int(result[1])
        retry_after = int(result[2])
        remaining = max(0, self.max_requests - count)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        return {"limit": self.max_requests, "remaining": remaining}
