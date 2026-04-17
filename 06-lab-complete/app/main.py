"""Production-ready AI agent for Day 12."""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import require_api_key
from app.config import settings
from app.cost_guard import RedisCostGuard
from app.rate_limiter import RedisRateLimiter
from utils.mock_llm import ask as llm_ask


START_TIME = time.time()
SHUTDOWN_STATE = {"received": False, "signal": None}
LOGGER = logging.getLogger("day12.agent")


def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(message)s")


def log_event(event: str, **fields: object) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    LOGGER.info(json.dumps(payload, ensure_ascii=True))


configure_logging()


class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    timestamp: str
    history_length: int
    rate_limit_remaining: int
    budget_remaining_usd: float


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 2)


def _conversation_key(user_id: str) -> str:
    return f"conversation:{user_id}"


async def append_history(redis_client: redis.Redis, user_id: str, role: str, content: str) -> None:
    entry = json.dumps(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        ensure_ascii=True,
    )
    key = _conversation_key(user_id)
    pipeline = redis_client.pipeline(transaction=True)
    pipeline.rpush(key, entry)
    pipeline.ltrim(key, -settings.history_limit, -1)
    pipeline.expire(key, settings.conversation_ttl_seconds)
    await pipeline.execute()


async def read_history(redis_client: redis.Redis, user_id: str) -> list[dict[str, str]]:
    raw_messages = await redis_client.lrange(_conversation_key(user_id), 0, -1)
    return [json.loads(item) for item in raw_messages]


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    await redis_client.ping()

    app.state.redis = redis_client
    app.state.rate_limiter = RedisRateLimiter(redis_client, settings.rate_limit_per_minute, 60)
    app.state.cost_guard = RedisCostGuard(redis_client, settings.monthly_budget_usd)
    app.state.ready = True

    log_event(
        "startup",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        redis_url=settings.redis_url,
    )

    try:
        yield
    finally:
        app.state.ready = False
        log_event("shutdown", signal=SHUTDOWN_STATE["signal"])
        close_method = getattr(redis_client, "aclose", None) or getattr(redis_client, "close", None)
        if close_method is not None:
            result = close_method()
            if asyncio.iscoroutine(result):
                await result


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        log_event("request_error", method=request.method, path=request.url.path)
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    log_event(
        "request_complete",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.get("/", tags=["Info"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "health": "GET /health",
            "ready": "GET /ready",
            "ask": "POST /ask",
            "history": "GET /history/{user_id}",
            "usage": "GET /usage/{user_id}",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(body: AskRequest, request: Request, _api_key: str = Depends(require_api_key)):
    redis_client: redis.Redis = request.app.state.redis
    rate_limiter: RedisRateLimiter = request.app.state.rate_limiter
    cost_guard: RedisCostGuard = request.app.state.cost_guard

    rate_status = await rate_limiter.check(body.user_id)
    await cost_guard.check_budget(body.user_id)

    await append_history(redis_client, body.user_id, "user", body.question)
    answer = await asyncio.to_thread(llm_ask, body.question)
    await append_history(redis_client, body.user_id, "assistant", answer)

    input_tokens = _estimate_tokens(body.question)
    output_tokens = _estimate_tokens(answer)
    usage = await cost_guard.record_usage(body.user_id, input_tokens, output_tokens)
    history = await read_history(redis_client, body.user_id)

    log_event(
        "agent_answered",
        user_id=body.user_id,
        history_length=len(history),
        remote_addr=request.client.host if request.client else "unknown",
    )

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        history_length=len(history),
        rate_limit_remaining=rate_status["remaining"],
        budget_remaining_usd=usage["budget_remaining_usd"],
    )


@app.get("/history/{user_id}", tags=["Agent"])
async def get_history(user_id: str, request: Request, _api_key: str = Depends(require_api_key)):
    redis_client: redis.Redis = request.app.state.redis
    history = await read_history(redis_client, user_id)
    return {"user_id": user_id, "messages": history, "count": len(history)}


@app.get("/usage/{user_id}", tags=["Agent"])
async def get_usage(user_id: str, request: Request, _api_key: str = Depends(require_api_key)):
    cost_guard: RedisCostGuard = request.app.state.cost_guard
    return await cost_guard.get_usage(user_id)


@app.get("/health", tags=["Operations"])
async def health(request: Request):
    redis_client: redis.Redis | None = getattr(request.app.state, "redis", None)
    redis_ok = False
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    return {
        "status": "ok",
        "environment": settings.environment,
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "redis_connected": redis_ok,
        "shutting_down": SHUTDOWN_STATE["received"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
async def ready(request: Request):
    if not getattr(request.app.state, "ready", False):
        raise HTTPException(status_code=503, detail="Application is not ready.")

    redis_client: redis.Redis = request.app.state.redis
    try:
        await redis_client.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Redis is not ready.") from exc

    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}


def _handle_signal(signum, _frame) -> None:
    SHUTDOWN_STATE["received"] = True
    SHUTDOWN_STATE["signal"] = signum
    log_event("signal_received", signum=signum)


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
