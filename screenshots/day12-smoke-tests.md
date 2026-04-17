# Day12 Smoke Test Evidence

## Local checks

- `GET http://localhost:8000/health` -> `200`
- `GET http://localhost:8000/ready` -> `200`
- `POST http://localhost:8000/ask` without API key -> `401`
- `POST http://localhost:8000/ask` with API key -> `200`
- `GET http://localhost:8000/history/student-1` -> `200`
- `GET http://localhost:8000/usage/student-1` -> `200`
- request `11` for `rate-limit-user` in the same minute -> `429`
- seeded budget record for `budget-test-user` -> `402`

## Public checks

- `GET https://day12-production-agent-production.up.railway.app/health` -> `200`
- `POST https://day12-production-agent-production.up.railway.app/ask` without API key -> `401`
- `POST https://day12-production-agent-production.up.railway.app/ask` with API key -> `200`

## Sample public response

```json
{
  "user_id": "railway-user",
  "question": "What is deployment?",
  "answer": "Deployment is the process of shipping your application to a reachable environment and verifying it stays healthy.",
  "model": "mock-gpt-4o-mini",
  "history_length": 2,
  "rate_limit_remaining": 9
}
```
