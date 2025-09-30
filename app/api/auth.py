"""
认证相关路由
"""
import logging
from flask import Blueprint, request, session, redirect, url_for, jsonify, current_app
from app.services.ebay_service import EbayService
from app.utils.decorators import handle_api_errors

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
@handle_api_errors
def login():
    """eBay OAuth登录"""
    # 检查本地调试token
    debug_token = current_app.config.get('EBAY_USER_ACCESS_TOKEN')
    if debug_token:
        session['ebay_token'] = {
            'access_token': debug_token,
            'token_type': 'Bearer',
            'debug_mode': True
        }
        return redirect(url_for('main.index'))
    
    # 检查必要的配置
    required_configs = ['EBAY_APP_ID', 'EBAY_CERT_ID', 'EBAY_RU_NAME']
    missing_configs = [config for config in required_configs if not current_app.config.get(config)]
    
    if missing_configs:
        logger.error(f"Missing eBay API credentials: {missing_configs}")
        return jsonify({'error': 'eBay API設定が不完全です'}), 500
    
    # 构建OAuth URL并重定向
    ebay_service = EbayService()
    auth_url = ebay_service.build_oauth_url(current_app.config['EBAY_RU_NAME'])
    return redirect(auth_url)


@auth_bp.route('/callback')
@handle_api_errors
def callback():
    """OAuth回调处理"""
    logger.info(f"OAuth callback received: {request.args}")
    
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # 处理OAuth错误
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        return jsonify({'error': f'eBay OAuth エラー: {error} - {error_description}'}), 400
    
    if not code:
        logger.error(f"Authorization code not found. Received parameters: {dict(request.args)}")
        return jsonify({'error': '認証コードが見つかりません'}), 400
    
    # 交换访问令牌
    ebay_service = EbayService()
    token_data = ebay_service.exchange_code_for_token(code, current_app.config['EBAY_RU_NAME'])
    
    if not token_data:
        return jsonify({'error': 'アクセストークンの取得に失敗しました'}), 500
    
    # 保存token到session
    session['ebay_token'] = {
        'access_token': token_data.get('access_token'),
        'refresh_token': token_data.get('refresh_token'),
        'token_type': token_data.get('token_type', 'Bearer'),
        'expires_in': token_data.get('expires_in')
    }
    
    logger.info("OAuth authentication successful")
    return redirect(url_for('main.index'))


@auth_bp.route('/logout')
def logout():
    """登出"""
    session.pop('ebay_token', None)
    logger.info("User logged out")
    return redirect(url_for('main.index'))


@auth_bp.route('/status')
def auth_status():
    """检查认证状态"""
    if 'ebay_token' in session:
        token_info = session['ebay_token']
        return jsonify({
            'authenticated': True,
            'debug_mode': token_info.get('debug_mode', False),
            'token_type': token_info.get('token_type', 'Bearer')
        })
    else:
        return jsonify({'authenticated': False})
