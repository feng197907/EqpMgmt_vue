# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_TYPE=sqlite \
    PORT=5000 \
    TZ=Asia/Shanghai \
    PIP_INDEX_URL=http://mirrors.tencentyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.tencentyun.com \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=5

WORKDIR /app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install --retries ${PIP_RETRIES} --default-timeout ${PIP_DEFAULT_TIMEOUT} -r requirements.txt

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . .

RUN mkdir -p uploads logs /data

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]