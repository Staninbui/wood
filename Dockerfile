# マルチステージビルドで最適化
FROM python:3.12-slim as builder

# 依存関係のインストール用
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番環境用イメージ
FROM python:3.12-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# セキュリティ: 非rootユーザーで実行
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 環境変数
ENV PYTHONUNBUFFERED=True \
    PYTHONDONTWRITEBYTECODE=True \
    PATH="/home/appuser/.local/bin:$PATH" \
    APP_HOME=/app

# 作業ディレクトリ設定
WORKDIR $APP_HOME

# 依存関係をコピー
COPY --from=builder /root/.local /home/appuser/.local

# アプリケーションコードをコピー
COPY --chown=appuser:appgroup . .

# 権限設定
RUN chown -R appuser:appgroup $APP_HOME

# 非rootユーザーに切り替え
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# 启动完整应用，使用优化的配置
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --worker-class gevent --worker-connections 500 --timeout 120 --log-level info app:app
