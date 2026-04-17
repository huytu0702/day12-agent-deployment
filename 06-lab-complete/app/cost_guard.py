"""Redis-backed monthly budget guard."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException


PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.00060


class RedisCostGuard:
    def __init__(self, redis_client, monthly_budget_usd: float):
        self.redis = redis_client
        self.monthly_budget_usd = monthly_budget_usd

    def _key(self, user_id: str, now: datetime | None = None) -> str:
        current = now or datetime.now(timezone.utc)
        return f"budget:{current.strftime('%Y-%m')}:{user_id}"

    @staticmethod
    def _expires_at(now: datetime | None = None) -> int:
        current = now or datetime.now(timezone.utc)
        if current.month == 12:
            next_month = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_month = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
        return int((next_month + timedelta(days=2)).timestamp())

    @staticmethod
    def _cost_for(input_tokens: int, output_tokens: int) -> float:
        return round(
            (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
            + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS,
            6,
        )

    async def check_budget(self, user_id: str) -> dict[str, float]:
        key = self._key(user_id)
        spent = float(await self.redis.hget(key, "spent_usd") or 0.0)
        if spent >= self.monthly_budget_usd:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Monthly budget exceeded",
                    "used_usd": round(spent, 6),
                    "budget_usd": self.monthly_budget_usd,
                    "resets_at": "start of next UTC month",
                },
            )
        return {
            "spent_usd": round(spent, 6),
            "budget_remaining_usd": round(self.monthly_budget_usd - spent, 6),
        }

    async def record_usage(self, user_id: str, input_tokens: int, output_tokens: int) -> dict[str, float]:
        key = self._key(user_id)
        cost = self._cost_for(input_tokens, output_tokens)

        pipeline = self.redis.pipeline(transaction=True)
        pipeline.hincrbyfloat(key, "spent_usd", cost)
        pipeline.hincrby(key, "input_tokens", input_tokens)
        pipeline.hincrby(key, "output_tokens", output_tokens)
        pipeline.hincrby(key, "request_count", 1)
        pipeline.expireat(key, self._expires_at())
        results = await pipeline.execute()

        spent_total = round(float(results[0]), 6)
        return {
            "spent_usd": spent_total,
            "budget_usd": self.monthly_budget_usd,
            "budget_remaining_usd": round(max(0.0, self.monthly_budget_usd - spent_total), 6),
            "request_count": int(results[3]),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    async def get_usage(self, user_id: str) -> dict[str, float]:
        key = self._key(user_id)
        usage = await self.redis.hgetall(key)

        spent = float(usage.get("spent_usd", 0.0))
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        request_count = int(usage.get("request_count", 0))

        return {
            "user_id": user_id,
            "month": datetime.now(timezone.utc).strftime("%Y-%m"),
            "spent_usd": round(spent, 6),
            "budget_usd": self.monthly_budget_usd,
            "budget_remaining_usd": round(max(0.0, self.monthly_budget_usd - spent), 6),
            "request_count": request_count,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
