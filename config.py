import os
from datetime import timedelta

class Config:
    """基本設定クラス"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    
    # eBay API設定
    EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
    EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID')
    EBAY_RU_NAME = os.environ.get('EBAY_RU_NAME')
    
    # セッション設定
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # アプリケーション設定
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # ワーカー設定（CPU集約的タスク用）
    MAX_WORKERS = os.environ.get('MAX_WORKERS', 4)
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', 300))  # 5分

class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    
    # Gunicorn設定
    WORKERS = int(os.environ.get('WEB_CONCURRENCY', 2))
    WORKER_CLASS = 'gevent'
    WORKER_CONNECTIONS = 1000
    
    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    SESSION_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
