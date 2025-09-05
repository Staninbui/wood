# マルチステージビルドで最適化
FROM python:3.11-slim as builder

# 依存関係のインストール用
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番環境用イメージ
FROM python:3.11-slim

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
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Gunicornでアプリケーション起動
CMD exec gunicorn --config gunicorn.conf.py app:app
