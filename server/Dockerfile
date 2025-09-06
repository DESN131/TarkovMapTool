FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安装系统依赖（可按需精简）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 先只拷贝依赖文件，利用缓存
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 再拷贝代码
COPY TKFServer.py ./TKFServer.py

EXPOSE 1688

# 缺省用 4 workers，按核数可调；输出到 stdout/stderr，便于 docker logs
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:1688", "TKFServer:app", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--access-logformat", "%(h)s %(t)s \"%(r)s\" %(s)s %(b)s worker=%(p)s time=%(L)s" ]
