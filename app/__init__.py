"""
Flask应用工厂模式
"""
import os
import logging
from flask import Flask
from config import config


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config[config_name]
    
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化配置
    config_class.init_app(app)
    
    # 创建必要的目录
    create_directories(app)
    
    # 注册组件
    register_blueprints(app)
    register_error_handlers(app)
    register_context_processors(app)
    
    # 配置日志
    configure_logging(app)
    
    with app.app_context():
        app.logger.info('Wood application startup')
    
    return app


def create_directories(app):
    """创建必要的目录"""
    directories = [
        app.config.get('UPLOAD_FOLDER', 'uploads'),
        app.config.get('TEMP_FOLDER', 'temp'),
        'logs'
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            app.logger.info(f'Created directory: {directory}')


def configure_logging(app):
    """配置日志"""
    if not app.debug and not app.testing:
        # 生产环境日志配置
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/wood.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Wood application startup')


def register_blueprints(app):
    """注册蓝图"""
    from app.api.auth import auth_bp
    from app.api.reports import reports_bp
    from app.api.tasks import tasks_bp
    from app.api.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')


def register_error_handlers(app):
    """注册错误处理器"""
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)


def register_context_processors(app):
    """注册上下文处理器"""
    @app.context_processor
    def inject_config():
        return {
            'app_name': 'Wood - eBay商品管理系统',
            'version': '2.0.0'
        }
