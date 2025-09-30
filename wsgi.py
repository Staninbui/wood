"""
WSGI入口文件 - 用于生产环境部署
"""
import os
from app import create_app

# 创建应用实例
application = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    application.run()
