"""
开发环境配置
"""
from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    
    DEBUG = True
    TESTING = False
    
    # 开发环境下禁用HTTPS要求
    SESSION_COOKIE_SECURE = False
    
    # 开发环境日志配置
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境特殊配置
    EXPLAIN_TEMPLATE_LOADING = True
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        
        # 开发环境特殊初始化
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
