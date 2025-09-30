"""
基础配置类
"""
import os
from datetime import timedelta


class BaseConfig:
    """基础配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    
    # eBay API配置
    EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
    EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID')
    EBAY_RU_NAME = os.environ.get('EBAY_RU_NAME')
    EBAY_USER_ACCESS_TOKEN = os.environ.get('EBAY_USER_ACCESS_TOKEN')  # 调试用
    
    # eBay API端点
    EBAY_OAUTH_BASE_URL = 'https://auth.ebay.com/oauth2/authorize'
    EBAY_TOKEN_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
    EBAY_FEED_API_BASE_URL = 'https://api.ebay.com/sell/feed/v1'
    EBAY_TRADING_API_URL = 'https://api.ebay.com/ws/api.dll'
    EBAY_SCOPES = ['https://api.ebay.com/oauth/api_scope/sell.inventory']
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 应用配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # 性能配置
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', 300))  # 5分钟
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        for folder in [BaseConfig.UPLOAD_FOLDER, BaseConfig.TEMP_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def get_ebay_api_endpoints(self):
        """获取eBay API端点配置"""
        return {
            'oauth_base_url': self.EBAY_OAUTH_BASE_URL,
            'token_url': self.EBAY_TOKEN_URL,
            'feed_api_base_url': self.EBAY_FEED_API_BASE_URL,
            'trading_api_url': self.EBAY_TRADING_API_URL,
            'inventory_report_url': f'{self.EBAY_FEED_API_BASE_URL}/inventory_task',
            'feed_task_url': f'{self.EBAY_FEED_API_BASE_URL}/task'
        }
