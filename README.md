# Lab 12 - Complete Production Agent

This repository snapshot is centered on the final part I completed: `06-lab-complete`.
It contains the production-ready FastAPI agent with Redis-backed state, Docker packaging, local load balancing, and cloud deployment config.

## What is included

- `app/main.py`: FastAPI app with `/health`, `/ready`, `/ask`, `/history/{user_id}`, `/usage/{user_id}`
- `app/auth.py`: API key authentication via `X-API-Key`
- `app/rate_limiter.py`: Redis sliding-window rate limit at `10 req/min/user`
- `app/cost_guard.py`: Redis monthly budget guard at `$10/month/user`
- `app/config.py`: environment-driven settings for local and production runs
- `check_production_ready.py`: automated readiness checks for the final submission
- `docker-compose.yml`: local stack with `agent + redis + nginx`
- `Dockerfile` and `nginx.conf`: multi-stage image, non-root runtime, healthcheck, reverse proxy
- `.env.example` and `utils/mock_llm.py`: local configuration template and offline mock LLM
- `railway.toml` and `render.yaml`: cloud deployment config for Railway and Render

## Final submission

- Final project folder: [06-lab-complete](06-lab-complete/README.md)
- Deployment notes: [DEPLOYMENT.md](DEPLOYMENT.md)
- Mission answers: [MISSION_ANSWERS.md](MISSION_ANSWERS.md)
- Public Railway URL: `https://day12-production-agent-production.up.railway.app`
- Evidence files: [screenshots/day12-railway-root.png](screenshots/day12-railway-root.png), [screenshots/day12-railway-health.png](screenshots/day12-railway-health.png), [screenshots/day12-smoke-tests.md](screenshots/day12-smoke-tests.md)

## How to run

See the full run guide in [06-lab-complete/README.md](06-lab-complete/README.md).
