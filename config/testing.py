"""
测试环境配置
"""
from .base import BaseConfig


class TestingConfig(BaseConfig):
    """测试环境配置"""
    
    DEBUG = True
    TESTING = True
    
    # 测试环境下禁用HTTPS要求
    SESSION_COOKIE_SECURE = False
    
    # 测试环境特殊配置
    WTF_CSRF_ENABLED = False
    
    # 使用内存数据库进行测试（如果需要）
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
