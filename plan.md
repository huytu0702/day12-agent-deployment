# Plan Hoan Thanh Day 12 Lab

## Muc tieu cuoi cung

Ban can nop 1 GitHub repository co du 4 nhom ket qua:

1. `MISSION_ANSWERS.md` tra loi bai tap Part 1-5.
2. Project hoan chinh trong `06-lab-complete/` dat tieu chi production-ready.
3. `DEPLOYMENT.md` chua public URL, lenh test, bien moi truong va screenshot.
4. Public URL deploy thuc su hoat dong.

Theo rubric, phan quan trong nhat la:

- Agent chay duoc qua REST API
- Dockerfile multi-stage
- `docker-compose.yml` co agent + redis
- Auth bang API key
- Rate limit `10 req/min`
- Cost guard `$10/thang/user`
- `GET /health` va `GET /ready`
- Graceful shutdown
- Stateless design, luu state trong Redis
- Khong hardcode secret
- Deploy len Railway hoac Render

## Nen lam o dau

Lam truc tiep trong thu muc `06-lab-complete/`.

Ly do:

- Thu muc nay da co skeleton san: `Dockerfile`, `docker-compose.yml`, `.env.example`, `railway.toml`, `render.yaml`, `check_production_ready.py`.
- Day la noi duoc dung de ghep tat ca concepts cua Day 12 thanh bai nop cuoi.

## Gap hien tai cua skeleton

Nhung diem con thieu hoac chua dung voi rubric:

- `06-lab-complete/app/main.py` dang rate limit bang memory, chua dung Redis.
- Cost guard dang tinh theo ngay va theo process, chua dat yeu cau `$10/thang/user`.
- Chua co `app/auth.py`, `app/rate_limiter.py`, `app/cost_guard.py` du dung nhu checklist nop bai.
- Chua co luu conversation history trong Redis, nen chua stateless.
- `docker-compose.yml` moi co `agent + redis`, chua co load balancer.
- Chua thay `MISSION_ANSWERS.md`, `DEPLOYMENT.md`, folder `screenshots/`.
- Can kiem tra `.gitignore` de chac chan khong commit `.env`.

## Thu tu thuc hien de hoan thanh bai

### Phase 1: Hoan thanh Part 1-5 va ghi dap an

Muc tieu: tao `MISSION_ANSWERS.md`.

1. Part 1:
- Doc va chay `01-localhost-vs-production/develop/app.py`.
- Liet ke it nhat 5 anti-patterns.
- So sanh voi `01-localhost-vs-production/production/app.py`.
- Dien bang `Feature | Develop | Production | Why Important?`

2. Part 2:
- Doc `02-docker/develop/Dockerfile`.
- Build image develop va ghi lai image size.
- Doc `02-docker/production/Dockerfile`.
- Build image production, so sanh size, neu duoc thi mo ta multi-stage build va stack trong `docker-compose.yml`.

3. Part 3:
- Chon 1 nen tang: Railway hoac Render.
- Uu tien Railway neu muon lam nhanh.
- Deploy thanh cong va lay public URL.

4. Part 4:
- Chay va test auth, rate limiting, cost guard trong folder `04-api-gateway`.
- Ghi lai output test vao `MISSION_ANSWERS.md`.

5. Part 5:
- Chay va hieu health check, readiness, graceful shutdown, stateless design.
- Ghi note implementation va test results vao `MISSION_ANSWERS.md`.

Chi can nop dap an ro rang, co test result va giai thich ngan gon. Khong can viet qua dai.

### Phase 2: Hoan thien source code trong `06-lab-complete`

Muc tieu: bien skeleton thanh bai nop dat rubric.

1. Sua cau truc app:
- Tao hoac bo sung cac file:
  - `06-lab-complete/app/main.py`
  - `06-lab-complete/app/config.py`
  - `06-lab-complete/app/auth.py`
  - `06-lab-complete/app/rate_limiter.py`
  - `06-lab-complete/app/cost_guard.py`

2. Config:
- Tat ca config doc tu env vars.
- Toi thieu phai co:
  - `PORT`
  - `REDIS_URL`
  - `AGENT_API_KEY`
  - `LOG_LEVEL`
  - `RATE_LIMIT_PER_MINUTE`
  - `MONTHLY_BUDGET_USD`

3. Endpoint va logic chinh:
- `GET /health` tra `200`
- `GET /ready` check Redis va tra `200` hoac `503`
- `POST /ask`:
  - bat buoc `X-API-Key`
  - co `user_id`
  - rate limit theo user
  - budget limit theo user/thang
  - doc va ghi conversation history vao Redis
  - goi mock LLM
  - tra response hop le

4. Bao mat:
- Khong de secret hardcode trong code.
- `.env` khong duoc commit.
- Chi commit `.env.example`.

5. Reliability:
- Bat SIGTERM va dong ket noi cleanly.
- Structured JSON logging.
- Khong luu state trong bien global/memory cho conversation, rate limit, budget.

### Phase 3: Docker va local verification

Muc tieu: chay duoc local truoc khi deploy.

1. Dockerfile:
- Multi-stage build
- Dung base image slim
- Co non-root user
- Co `HEALTHCHECK`
- Image muc tieu `< 500 MB`

2. Docker Compose:
- Toi thieu co `agent` va `redis`
- Tot hon neu bo sung `nginx` neu ban muon the hien phan load balancing ro hon

3. Test local can lam:
- `docker compose up --build`
- `curl http://localhost:8000/health`
- `curl http://localhost:8000/ready`
- Goi `/ask` khong co key, phai ra `401`
- Goi `/ask` co key, phai ra `200`
- Goi lap > 10 lan/phut, phai ra `429`

4. Chay script check:
- `cd 06-lab-complete`
- `python check_production_ready.py`

Muc tieu toi thieu: script nay pass hoan toan, sau do test tay them cho rate limit, budget, conversation history.

### Phase 4: Deploy cloud

Muc tieu: co public URL hoat dong.

Lua chon nhanh nhat:

1. Railway:
- `npm i -g @railway/cli`
- `railway login`
- `railway init`
- set env vars
- `railway up`
- `railway domain`

2. Render:
- Push len GitHub
- Connect repo trong Render
- Dung `render.yaml`
- Set env vars trong dashboard

Sau khi deploy, phai test public URL:

- `/health` tra `200`
- `/ask` khong co auth tra `401`
- `/ask` co auth tra `200`

### Phase 5: Hoan thien file nop bai

Can tao them o root repo:

1. `MISSION_ANSWERS.md`
- Tra loi day du Part 1-5
- Co test results, image size, public URL, ghi chu implementation

2. `DEPLOYMENT.md`
- Public URL
- Nen tang deploy
- Lenh test
- Danh sach env vars da set
- Link hoac tham chieu screenshot

3. `screenshots/`
- Dashboard deploy
- Service running
- Ket qua test

4. `README.md`
- Kiem tra lai cho ro cach chay local va deploy

## Checklist hoan thanh toi thieu

Ban co the dung checklist nay de tu danh dau:

- [ ] Tao `MISSION_ANSWERS.md`
- [ ] Hoan thien `06-lab-complete/app/main.py`
- [ ] Tao `06-lab-complete/app/auth.py`
- [ ] Tao `06-lab-complete/app/rate_limiter.py`
- [ ] Tao `06-lab-complete/app/cost_guard.py`
- [ ] Chuyen conversation history sang Redis
- [ ] Rate limit dat `10 req/min/user`
- [ ] Cost guard dat `$10/thang/user`
- [ ] Co `GET /health`
- [ ] Co `GET /ready`
- [ ] Co graceful shutdown
- [ ] Khong hardcode secrets
- [ ] `.env` duoc ignore
- [ ] Docker build thanh cong
- [ ] `docker compose up` chay thanh cong
- [ ] `python check_production_ready.py` pass
- [ ] Deploy len Railway hoac Render
- [ ] Tao `DEPLOYMENT.md`
- [ ] Them screenshot vao `screenshots/`
- [ ] Push GitHub repo va test lai public URL

## Thu tu uu tien neu thoi gian gap

Neu ban can toi uu de qua bai nhanh:

1. Hoan thien `06-lab-complete` cho chay local.
2. Dam bao auth, Redis state, rate limit, cost guard, health, ready.
3. Dockerize va test local.
4. Deploy Railway.
5. Viet `MISSION_ANSWERS.md`.
6. Viet `DEPLOYMENT.md` va chup screenshot.

## Dinh nghia "xong bai"

Ban duoc xem la xong khi dat dong thoi 4 dieu kien:

1. Repo co day du source code va docs nop bai.
2. `06-lab-complete` chay local bang Docker Compose.
3. Public URL truy cap duoc va pass cac test co ban.
4. Khong con secret hardcode hoac file `.env` bi commit.
