# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Secrets bị hardcode trực tiếp trong code: `OPENAI_API_KEY` và `DATABASE_URL`.
2. Không có config management tập trung, dùng hằng số trong file thay vì environment variables.
3. `DEBUG = True` và `reload=True`, không phù hợp cho production.
4. Log bằng `print()` và còn log luôn secret ra console.
5. Không có `GET /health` để platform biết khi nào cần restart container.
6. Port bị hardcode là `8000`, không đọc `PORT` từ môi trường.
7. Bind vào `localhost` nên không nhận traffic từ ngoài container/cloud.
8. Không có graceful shutdown hoặc lifecycle hooks.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trực tiếp trong `app.py` | Tập trung trong `config.py`, đọc từ env vars | Dễ đổi giữa local/staging/prod, không lộ secret |
| Host binding | `localhost` | `0.0.0.0` | Container/cloud chỉ route được nếu bind ra ngoài |
| Port | Cứng `8000` | Đọc từ `PORT` env var | Railway/Render inject port động |
| Logging | `print()` | Structured JSON logging | Dễ parse và monitor trên platform |
| Secret handling | Log ra API key | Không log secret, validate config | Tránh lộ credentials |
| Health check | Không có | Có `/health` | Liveness probe để restart khi app lỗi |
| Readiness check | Không có | Có `/ready` | Load balancer chỉ route vào instance đã sẵn sàng |
| Graceful shutdown | Không có | Có `lifespan` + `SIGTERM` handler | Giảm rơi request khi deploy/restart |
| CORS | Không cấu hình | Có `CORSMiddleware` | Hạn chế origin và kiểm soát bề mặt tấn công |
| Validation | Nhận input đơn giản | Check body và raise `HTTPException` | Trả lỗi rõ ràng, tránh request bẩn |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. `COPY requirements.txt` trước để tận dụng Docker layer cache. Khi code đổi nhưng dependencies không đổi thì layer `pip install` không cần build lại.
4. `CMD` là lệnh mặc định, có thể bị override dễ dàng khi `docker run`. `ENTRYPOINT` biến container thành một executable cố định hơn; thường dùng khi muốn ép container luôn chạy một binary cụ thể.

### Exercise 2.2: Build and run result
- Lệnh build chạy thành công:

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent-develop .
```

- Image size thực tế:

```text
my-agent-develop:latest = 1.66GB
```


- Khi test runtime, endpoint `/ask` của bản develop nhận `question` dưới dạng query parameter, không phải JSON body:

```bash
curl -X POST "http://localhost:8001/ask?question=What%20is%20Docker%3F"
```

Response:

```json
{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}
```

### Exercise 2.3: Image size comparison
- Develop: 1.66GB
- Production: 236.44MB
- Difference: giảm ~7 lần

Lệnh build production đã chạy thành công:

```bash
docker build -f 02-docker/production/Dockerfile -t my-agent-advanced .
```

Test runtime production:

```bash
docker run -p 8002:8000 -e ENVIRONMENT=production my-agent-advanced
```

Kết quả:

```text
GET /health  -> 200 OK
POST /ask    -> trả response hợp lệ khi gửi JSON body đúng format
```

Response mẫu từ `POST /ask`:

```json
{"answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
```

### Exercise 2.3: Multi-stage build analysis
- Stage 1 `builder`: cài build dependencies (`gcc`, `libpq-dev`) và `pip install` packages.
- Stage 2 `runtime`: chỉ copy site-packages và source code cần thiết để chạy app.
- Image nhỏ hơn vì runtime không mang theo compiler, apt cache và build tool từ stage builder.
- Runtime dùng `python:3.11-slim`, non-root user `appuser`, có `HEALTHCHECK`.

### Exercise 2.4: Docker Compose stack
Services trong `02-docker/production/docker-compose.yml`:
- `agent`: FastAPI app.
- `redis`: cache/session/rate-limit store.
- `qdrant`: vector database.
- `nginx`: reverse proxy và load balancer.

Luồng traffic:
- Client gọi `nginx`.
- `nginx` proxy sang `agent`.
- `agent` dùng `redis` và `qdrant` qua internal network.

Nhận xét:
- Kiến trúc đúng hướng production stack.
- Compose này có đủ `agent + redis + qdrant + nginx`.
- `agent` build từ target `runtime` của multi-stage Dockerfile.
- Repo hiện chưa có `02-docker/production/.env.local`, nên muốn chạy `docker compose up` đúng như file mẫu thì cần bổ sung file env này trước.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Nền tảng tôi chọn và đã deploy thật là `Railway`.
- Railway CLI version: `4.38.0`
- Tài khoản đăng nhập: `tufy2k4@gmail.com`
- Project đã tạo: `day12-cloud-deployment-lab`
- Service đã deploy: `day12-cloud-deployment-lab`
- Deployment ID: `1c10ee69-66cf-4699-aa65-14d0d003943c`
- Deployment status: `SUCCESS`
- Public URL:

```text
https://day12-cloud-deployment-lab-production.up.railway.app
```

- Screenshot bằng chứng deployment:

```text
screenshots/part3.png
```

- Link screenshot trong repo: [screenshots/part3.png](screenshots/part3.png)

Các lệnh đã dùng thực tế:

```bash
cd 03-cloud-deployment/railway
railway init -n day12-cloud-deployment-lab --json
railway up --detach --path-as-root . --message "Part 3 lab deploy"
railway domain --json
```

Kiểm tra HTTP thực tế sau deploy:

```text
GET /       -> 200 OK
GET /health -> 200 OK
POST /ask   -> 200 OK
```

Response mẫu từ Railway:

```json
{
  "status": "ok",
  "uptime_seconds": 23.6,
  "platform": "Railway",
  "timestamp": "2026-04-17T07:26:32.921140+00:00"
}
```

Response mẫu từ `POST /ask`:

```json
{
  "question": "What is deployment?",
  "answer": "Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được.",
  "platform": "Railway"
}
```

### Exercise 3.2: Compare `railway.toml` vs `render.yaml`
| Item | Railway | Render |
|------|---------|--------|
| Config file | `railway.toml` | `render.yaml` |
| Deploy style | CLI-first | GitHub Blueprint / IaC |
| Build | `builder = "NIXPACKS"` | `buildCommand: pip install -r requirements.txt` |
| Start command | `uvicorn app:app --host 0.0.0.0 --port $PORT` | giống Railway |
| Health check | `healthcheckPath = "/health"` | `healthCheckPath: /health` |
| Restart | `restartPolicyType = "ON_FAILURE"` | mặc định theo service của Render |
| Extra managed services | không khai báo Redis trong cùng file mẫu | khai báo luôn cả Redis service trong `render.yaml` |

### Deployment status note
- Public URL: `https://day12-cloud-deployment-lab-production.up.railway.app` (đã shutdown sau khi chạy để tiết kiệm resource cho Part 6)  
- Deployment đã chạy thành công trên Railway.
- Screenshot dashboard đã có trong repo: [screenshots/part3.png](screenshots/part3.png)

## Part 4: API Security

### Exercise 4.1: API key authentication
- API key được check trong hàm `verify_api_key()` của `04-api-gateway/develop/app.py`.
- Nếu thiếu key: trả `401`.
- Nếu sai key: trả `403`.
- Rotate key bằng cách đổi giá trị environment variable `AGENT_API_KEY`.

Test kết quả thực tế :

```text
NO_KEY
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}
HTTP_STATUS:401

WITH_KEY
{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
HTTP_STATUS:200
```

### Exercise 4.2: JWT authentication
JWT flow trong `04-api-gateway/production/auth.py`:
1. `POST /auth/token` nhận username/password.
2. `authenticate_user()` check demo credentials.
3. `create_token()` tạo JWT chứa `sub`, `role`, `iat`, `exp`.
4. `verify_token()` decode token ở các request protected.

Tuy nhiên, app production hiện đang lỗi middleware nên request HTTP thực tế bị `500` trước khi tới logic auth:

```text
AttributeError: 'MutableHeaders' object has no attribute 'pop'
```

Lỗi nằm ở:

```python
response.headers.pop("server", None)
```

### Exercise 4.3: Rate limiting
- Algorithm: `Sliding Window Counter` bằng `deque`.
- User limit: `10 requests / 60 giây`.
- Admin bypass bằng cách dùng `rate_limiter_admin` thay vì `rate_limiter_user`, hiện đang cho `100 requests / 60 giây`.

Do middleware của app production đang lỗi, tôi test trực tiếp module:

```text
RATE 1:ok:9 | 2:ok:8 | 3:ok:7 | 4:ok:6 | 5:ok:5 | 6:ok:4 | 7:ok:3 | 8:ok:2 | 9:ok:1 | 10:ok:0 | 11:err:429:{'error': 'Rate limit exceeded', 'limit': 10, 'window_seconds': 60, 'retry_after_seconds': 61}
```

Kết luận:
- Request thứ 11 bị chặn đúng với `429`.
- Rate limiting logic hoạt động, nhưng hiện mới là in-memory nên không scale qua nhiều instance.

### Exercise 4.4: Cost guard implementation
Hiện trạng của sample `cost_guard.py`:
- đang dùng in-memory,
- theo `ngày`,
- budget mặc định `$1/day/user`,
- chưa đúng yêu cầu cuối bài là `$10/month/user` với Redis.

Test trực tiếp module:

```text
BUDGET 402 {'error': 'Daily budget exceeded', 'used_usd': 1.5, 'budget_usd': 1.0, 'resets_at': 'midnight UTC'}
```

Approach đúng để làm production:
1. Dùng Redis key dạng `budget:{user_id}:{YYYY-MM}`.
2. Đọc chi phí hiện tại bằng `GET`.
3. Nếu `current + estimated_cost > 10` thì chặn request.
4. Nếu chưa vượt, cộng bằng `INCRBYFLOAT`.
5. Đặt TTL khoảng `32 ngày` để key tự hết hạn sau kỳ billing.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
Test thực tế với `05-scaling-reliability/develop/app.py`:

```text
HEALTH
{"status":"degraded","uptime_seconds":3.0,"version":"1.0.0","environment":"development","timestamp":"2026-04-17T07:02:01.813900+00:00","checks":{"memory":{"status":"degraded","used_percent":93.3}}}
HTTP_STATUS:200

READY
{"ready":true,"in_flight_requests":1}
HTTP_STATUS:200
```

Nhận xét:
- `/health` trả `200`, đúng vai trò liveness probe.
- `/ready` trả `200`, chứng tỏ app sẵn sàng nhận traffic.
- `health` có thể trả trạng thái `degraded` nhưng vẫn sống, đây là cách biểu diễn hợp lý.

### Exercise 5.2: Graceful shutdown
Code đã có các thành phần đúng hướng:
- `lifespan()` set `_is_ready = False` khi shutdown.
- Chờ `_in_flight_requests` về 0 hoặc timeout 30 giây.
- Bắt `SIGTERM` và `SIGINT`.
- `uvicorn.run(... timeout_graceful_shutdown=30)`.

Lưu ý:
- Tôi chưa xác minh end-to-end graceful shutdown trên Windows shell này, vì cơ chế terminate process tại đây không mô phỏng chuẩn tín hiệu container như Linux/Kubernetes.

### Exercise 5.3: Stateless design
`05-scaling-reliability/production/app.py` dùng Redis nếu kết nối được:
- `save_session()`
- `load_session()`
- `append_to_history()`

Nếu Redis không có, code fallback sang `_memory_store`, nghĩa là:
- app vẫn chạy demo được,
- nhưng không còn stateless thật sự.

Test local không có Redis:

```text
{"session_id":"c0a71c51-0344-4948-aa64-7347ec141661","question":"What is Docker?","served_by":"instance-a04ce2","storage":"in-memory"}
{"session_id":"c0a71c51-0344-4948-aa64-7347ec141661","question":"Why containers?","served_by":"instance-a04ce2","storage":"in-memory"}
```

Kết luận:
- Logic session/history hoạt động.
- Nhưng local test hiện đang chạy ở chế độ `in-memory`, chưa chứng minh được stateless qua nhiều instance.

### Exercise 5.4: Load balancing
`05-scaling-reliability/production/nginx.conf` khai báo:
- upstream `agent_cluster`
- proxy qua service `agent:8000`
- header `X-Served-By`
- `proxy_next_upstream error timeout http_503`

Ý nghĩa:
- Nginx sẽ phân phối request sang các agent instance.
- Nếu một instance lỗi hoặc timeout, request có thể chuyển sang upstream khác.

### Exercise 5.5: Test stateless
`test_stateless.py` được viết đúng ý tưởng:
1. tạo session,
2. gửi nhiều request liên tiếp,
3. theo dõi `served_by`,
4. kiểm tra history còn nguyên.

Tuy nhiên stack production hiện chưa chạy được as-is vì:

```text
05-scaling-reliability/production/docker-compose.yml
dockerfile: 05-scaling-reliability/advanced/Dockerfile
```

File `05-scaling-reliability/advanced/Dockerfile` hiện không tồn tại.

### Implementation notes summary
- Health/readiness: đã test được local.
- Graceful shutdown: code đã có, cần verify lại trên môi trường container Linux.
- Stateless design: đúng ý tưởng khi có Redis, nhưng sample hiện fallback về memory nếu thiếu Redis.
- Load balancing: Nginx config đã có.
- `test_stateless.py`: chưa chạy end-to-end được cho tới khi sửa docker-compose path.

## Final Project Update

- Final production-ready project completed in `06-lab-complete/`.
- Redis-backed `rate limit`, `monthly budget`, and `conversation history` are now implemented in the final app.
- Local production checker result: `20/20 checks passed`.
- Final public deployment URL:

```text
https://day12-production-agent-production.up.railway.app
```

- Public smoke test on `2026-04-17`:

```text
GET /health -> 200
POST /ask (no key) -> 401
POST /ask (with key) -> 200
```
