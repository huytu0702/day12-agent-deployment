# Lab 12 - Complete Production Agent

This folder contains the final Day 12 submission target: a production-ready FastAPI agent with Redis-backed state, Docker packaging, load-balanced local runtime, and Railway deployment config.

## What is included

- `app/main.py`: FastAPI app with `/health`, `/ready`, `/ask`, `/history/{user_id}`, `/usage/{user_id}`
- `app/auth.py`: API key authentication via `X-API-Key`
- `app/rate_limiter.py`: Redis sliding-window limit at `10 req/min/user`
- `app/cost_guard.py`: Redis monthly budget guard at `$10/month/user`
- `docker-compose.yml`: local stack with `agent + redis + nginx`
- `Dockerfile`: multi-stage image, non-root runtime, healthcheck
- `railway.toml` and `render.yaml`: cloud deployment config

## Required environment variables

Copy `.env.example` to `.env` for local work.

```bash
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
AGENT_API_KEY=replace-with-a-long-random-value
RATE_LIMIT_PER_MINUTE=10
MONTHLY_BUDGET_USD=10.0
ALLOWED_ORIGINS=*
```

## Run locally

```bash
docker compose up --build -d
```

Traffic goes through `nginx` on `http://localhost:8000`.

### Smoke test

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: day12-local-dev-key" \
  -d '{"user_id":"student-1","question":"What is deployment?"}'
```

### Expected behavior

- missing API key -> `401`
- valid API key -> `200`
- request 11 within one minute for the same `user_id` -> `429`
- user whose monthly budget is exhausted -> `402`

## Production readiness check

```bash
python check_production_ready.py
```

Expected result: `20/20 checks passed`.

## Railway deploy

This repository has already been deployed once with Railway CLI using this folder as root.

```bash
railway up --detach --path-as-root .
railway domain -s day12-production-agent
```

Current public URL is documented in the root [DEPLOYMENT.md](../DEPLOYMENT.md).
