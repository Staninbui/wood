"""
主要页面路由
"""
from flask import Blueprint, render_template, session, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页"""
    # 检查本地调试token
    debug_token = current_app.config.get('EBAY_USER_ACCESS_TOKEN')
    if debug_token:
        # 设置调试模式的session
        session['ebay_token'] = {
            'access_token': debug_token,
            'token_type': 'Bearer',
            'debug_mode': True
        }
        return render_template('dashboard.html')
    elif 'ebay_token' in session:
        return render_template('dashboard.html')
    return render_template('index.html')


@main_bp.route('/health')
def health_check():
    """健康检查端点"""
    from datetime import datetime
    from flask import jsonify
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'wood-ebay-app',
        'version': '2.0.0'
    }), 200
