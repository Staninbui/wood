# 多阶段构建优化
FROM python:3.11-slim as builder

# 依赖安装阶段
WORKDIR /app
COPY requirements/production.txt requirements/base.txt requirements/
RUN pip install --no-cache-dir --user -r requirements/production.txt

# 生产环境镜像
FROM python:3.11-slim

# 安装必要的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安全：使用非root用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 环境变量
ENV PYTHONUNBUFFERED=True \
    PYTHONDONTWRITEBYTECODE=True \
    PATH="/home/appuser/.local/bin:$PATH" \
    APP_HOME=/app \
    PYTHONHTTPSVERIFY=0 \
    CURL_CA_BUNDLE="" \
    REQUESTS_CA_BUNDLE="" \
    FLASK_ENV=production

# 工作目录设置
WORKDIR $APP_HOME

# 复制依赖
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY --chown=appuser:appgroup . .

# 创建必要的目录
RUN mkdir -p logs temp uploads && \
    chown -R appuser:appgroup $APP_HOME

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# 使用新的WSGI入口启动应用
CMD exec gunicorn -c gunicorn.conf.py wsgi:application
