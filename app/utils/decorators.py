"""
装饰器工具
"""
import functools
import logging
from flask import session, jsonify, request
from typing import Callable, Any

logger = logging.getLogger(__name__)


def login_required(f: Callable) -> Callable:
    """登录验证装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'ebay_token' not in session:
            if request.is_json:
                return jsonify({'error': 'ログインが必要です'}), 401
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def handle_api_errors(f: Callable) -> Callable:
    """API错误处理装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {f.__name__}: {e}")
            return jsonify({'error': f'入力エラー: {str(e)}'}), 400
        except ConnectionError as e:
            logger.error(f"Connection error in {f.__name__}: {e}")
            return jsonify({'error': 'eBay APIへの接続に失敗しました'}), 503
        except TimeoutError as e:
            logger.error(f"Timeout error in {f.__name__}: {e}")
            return jsonify({'error': 'リクエストがタイムアウトしました'}), 504
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({'error': f'予期しないエラーが発生しました: {str(e)}'}), 500
    return decorated_function


def validate_task_id(f: Callable) -> Callable:
    """任务ID验证装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        task_id = kwargs.get('task_id') or request.view_args.get('task_id')
        if not task_id or not isinstance(task_id, str) or len(task_id.strip()) == 0:
            return jsonify({'error': '有効なタスクIDが必要です'}), 400
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """简单的速率限制装饰器"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现更复杂的速率限制逻辑
            # 目前只是一个占位符
            return f(*args, **kwargs)
        return decorated_function
    return decorator
