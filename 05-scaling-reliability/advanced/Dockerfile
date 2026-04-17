FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system agent \
    && useradd --system --gid agent --create-home --home-dir /home/agent agent

RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    "uvicorn[standard]==0.30.0" \
    redis==5.0.8

COPY 05-scaling-reliability/production/app.py ./app.py
COPY 05-scaling-reliability/production/utils ./utils

RUN chown -R agent:agent /app

USER agent

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
