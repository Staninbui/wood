"""
生产环境配置
"""
import os
from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    
    DEBUG = False
    TESTING = False
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    
    # Gunicorn配置
    WORKERS = int(os.environ.get('WEB_CONCURRENCY', 2))
    WORKER_CLASS = 'gevent'
    WORKER_CONNECTIONS = 1000
    
    # 生产环境日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Cloud Run配置
    PORT = int(os.environ.get('PORT', 8080))
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        
        # 生产环境特殊初始化
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/wood.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Wood production startup')
