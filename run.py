"""
应用入口文件
"""
import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 本地开发服务器配置
    print("--- Wood eBay管理系统 开发服务器 ---")
    print("确保您的eBay应用的重定向URI设置为: http://127.0.0.1:8080/auth/callback")
    print("----------------------------------------")
    
    # 从环境变量获取端口，默认8080
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )
