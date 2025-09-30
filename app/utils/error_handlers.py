"""
错误处理器
"""
import logging
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json:
            return jsonify({'error': '不正なリクエストです'}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_json:
            return jsonify({'error': '認証が必要です'}), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({'error': 'アクセスが拒否されました'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({'error': 'リソースが見つかりません'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Server Error: {error}')
        if request.is_json:
            return jsonify({'error': 'サーバー内部エラーが発生しました'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        if request.is_json:
            return jsonify({'error': 'サービスが一時的に利用できません'}), 503
        return render_template('errors/503.html'), 503
    
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        """处理所有HTTP异常"""
        logger.error(f'HTTP Exception: {e}')
        if request.is_json:
            return jsonify({'error': e.description}), e.code
        return render_template('errors/generic.html', error=e), e.code
