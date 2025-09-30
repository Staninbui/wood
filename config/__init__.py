"""
配置管理模块
"""
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

__all__ = ['config', 'BaseConfig', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig']
