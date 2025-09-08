import os
import requests
import base64
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlencode, parse_qs
from flask import Flask, redirect, request, session, url_for, render_template, send_file, jsonify, Response
from io import BytesIO
import logging
from config import config
from xml_processor import XMLProcessor
import ssl
import urllib3
from progress_manager import progress_manager, TaskStatus
import time
import json

# SSL configuration to prevent recursion errors
import ssl
import urllib3
from urllib3.util import ssl_

# Completely disable SSL verification to prevent recursion
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey patch urllib3 to avoid SSL context creation issues
def patched_create_urllib3_context(ssl_version=None, cert_reqs=None, options=None, ciphers=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

ssl_.create_urllib3_context = patched_create_urllib3_context

# Create a custom requests session with SSL configuration
def create_ssl_session():
    session = requests.Session()
    session.verify = False
    # Use a custom adapter to bypass SSL issues
    from requests.adapters import HTTPAdapter
    from urllib3.poolmanager import PoolManager
    
    class NoSSLAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs['ssl_context'] = ssl.create_default_context()
            kwargs['ssl_context'].check_hostname = False
            kwargs['ssl_context'].verify_mode = ssl.CERT_NONE
            return super().init_poolmanager(*args, **kwargs)
    
    session.mount('https://', NoSSLAdapter())
    return session

# 環境に応じた設定を読み込み
config_name = os.environ.get('FLASK_ENV', 'development')
app_config = config.get(config_name, config['default'])

app = Flask(__name__)
app.config.from_object(app_config)

# ログ設定
logging.basicConfig(
    level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

# XML処理インスタンス
xml_processor = XMLProcessor(
    max_workers=int(app.config.get('MAX_WORKERS', 4)),
    timeout=int(app.config.get('TASK_TIMEOUT', 300))
)

# --- eBay API Configuration ---
# For local development, set these environment variables in your shell.
# On Cloud Run, set them as environment variables in the service configuration.
EBAY_APP_ID = os.getenv('EBAY_APP_ID')
EBAY_CERT_ID = os.getenv('EBAY_CERT_ID')
EBAY_RU_NAME = os.getenv('EBAY_RU_NAME')

# eBay OAuth 2.0 endpoints
EBAY_OAUTH_BASE_URL = 'https://auth.ebay.com/oauth2/authorize'
EBAY_TOKEN_URL = 'https://api.ebay.com/identity/v1/oauth2/token'

# eBay Feed API endpoints
EBAY_FEED_API_BASE_URL = 'https://api.ebay.com/sell/feed/v1'
EBAY_FEED_TASK_URL = f'{EBAY_FEED_API_BASE_URL}/task'
EBAY_FEED_DOWNLOAD_URL = f'{EBAY_FEED_API_BASE_URL}/task/{{task_id}}/download_result_file'

# eBay Feed API inventory task endpoints
EBAY_INVENTORY_REPORT_URL = f'{EBAY_FEED_API_BASE_URL}/inventory_task'
EBAY_INVENTORY_REPORT_DOWNLOAD_URL = f'{EBAY_FEED_API_BASE_URL}/inventory_task/{{task_id}}'
EBAY_INVENTORY_REPORT_MULTIPLE_DOWNLOAD_URL = f'{EBAY_FEED_API_BASE_URL}/inventory_task'

# eBay Trading API endpoints
EBAY_TRADING_API_URL = 'https://api.ebay.com/ws/api.dll'

# Define the required OAuth 2.0 scopes - using feed scope for reports
SCOPES = ['https://api.ebay.com/oauth/api_scope/sell.inventory']

@app.route('/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'wood-ebay-app'
    }), 200

@app.route('/')
def index():
    if 'ebay_token' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/login')
def login():
    if not all([EBAY_APP_ID, EBAY_CERT_ID, EBAY_RU_NAME]):
        return "Missing eBay API credentials in environment variables.", 500

    # Build OAuth 2.0 authorization URL
    params = {
        'client_id': EBAY_APP_ID,
        'redirect_uri': EBAY_RU_NAME,
        'response_type': 'code',
        'scope': ' '.join(SCOPES)
    }
    auth_url = f"{EBAY_OAUTH_BASE_URL}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # デバッグ情報を追加
    print(f"Callback received with args: {request.args}")
    print(f"Full request URL: {request.url}")
    
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # エラーパラメータがある場合、エラー情報を表示
    if error:
        return f"eBay OAuth Error: {error} - {error_description}", 400
    
    if not code:
        return f"Authorization code not found. Received parameters: {dict(request.args)}", 400

    # Prepare credentials for token exchange
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Exchange authorization code for access token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': EBAY_RU_NAME
    }

    try:
        ssl_session = create_ssl_session()
        response = ssl_session.post(EBAY_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Store token information in session
        session['ebay_token'] = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'expires_in': token_data.get('expires_in')
        }
        return redirect(url_for('index'))
    except requests.RequestException as e:
        return f"Error getting access token: {e}", 500

@app.route('/logout')
def logout():
    session.pop('ebay_token', None)
    return redirect(url_for('index'))

def create_inventory_task(access_token):
    """eBay Inventory Task を作成してアクティブリストを取得"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }

    payload = {
        "feedType": "LMS_ACTIVE_INVENTORY_REPORT",
        "schemaVersion": "1.0"
    }  
    
    print(f"=== Inventory Task API デバッグ情報 ===")
    print(f"URL: {EBAY_INVENTORY_REPORT_URL}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.post(EBAY_INVENTORY_REPORT_URL, headers=headers, json=payload)
        print(f"レスポンスステータスコード: {response.status_code}")
        print(f"レスポンスヘッダー: {response.headers}")
        print(f"レスポンス内容: {response.text}")
        
        # 202 はタスク作成成功を表す
        if response.status_code == 202:
            # Location ヘッダーから task_id を抽出
            location = response.headers.get('Location', '')
            print(f"Location ヘッダー: {location}")
            
            if location:
                # URL から task_id を抽出 (例: task-20-23232459833347 の task-20)
                task_id = location.split('/')[-1]
                print(f"抽出された task_id: {task_id}")
                
                return {
                    'taskId': task_id,
                    'status': 'CREATED',
                    'location': location
                }
            else:
                print("Location ヘッダーが見つかりません")
                return None
        else:
            response.raise_for_status()
            return response.json()
            
    except requests.RequestException as e:
        print(f"Inventory タスク作成失敗: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"エラーレスポンスステータスコード: {e.response.status_code}")
            print(f"エラーレスポンス内容: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"エラー JSON: {error_json}")
            except:
                pass
        return None

def get_inventory_task_status(access_token, task_id):
    """Inventory タスクステータスを取得"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.get(f'{EBAY_INVENTORY_REPORT_DOWNLOAD_URL.format(task_id=task_id)}', headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Inventory タスクステータス取得失敗: {e}")
        return None

def get_inventory_task_by_id(access_token, task_id):
    """task_id に基づいて単一の Inventory タスクステータスを取得"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    # GET /inventory_task/{task_id} エンドポイントを使用
    url = f'{EBAY_INVENTORY_REPORT_URL}/{task_id}'
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.get(url, headers=headers)
        print(f"単一タスクステータスチェックレスポンスステータスコード: {response.status_code}")
        print(f"単一タスクステータスチェックレスポンス内容: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"単一 Inventory タスクステータス取得失敗: {e}")
        return None

def get_recent_inventory_tasks(access_token, days=7):
    """最近指定日数内のすべての Inventory タスクを取得"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    # 日付範囲を計算
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # ISO 8601 形式でフォーマット (eBay APIが期待する3桁ミリ秒形式)
    date_from = start_date.strftime('%Y-%m-%dT%H:%M:%S') + f'.{start_date.microsecond // 1000:03d}Z'
    date_to = end_date.strftime('%Y-%m-%dT%H:%M:%S') + f'.{end_date.microsecond // 1000:03d}Z'
    
    params = {
        'date_range': f'{date_from}..{date_to}',
        'feed_type': 'LMS_ACTIVE_INVENTORY_REPORT',
        'limit': '200'
    }
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.get(EBAY_INVENTORY_REPORT_URL, headers=headers, params=params)
        print(f"最近のタスクリストレスポンスステータスコード: {response.status_code}")
        print(f"最近のタスクリストレスポンス内容: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"最近の Inventory タスクリスト取得失敗: {e}")
        return None

def download_inventory_result(access_token, task_id):
    """Inventory タスク結果をダウンロード"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    download_url = EBAY_INVENTORY_REPORT_DOWNLOAD_URL.format(task_id=task_id)
    print(f"=== Inventory Download API デバッグ情報 ===")
    print(f"URL: {download_url}")
    print(f"Task ID: {task_id}")
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.get(download_url, headers=headers)
        response.raise_for_status()
        return response.json()  # Inventory API は通常 JSON 形式で返す
    except requests.RequestException as e:
        print(f"Inventory 結果のダウンロードに失敗: {e}")
        return None

def parse_inventory_data(inventory_json):
    """Inventory API が返す JSON データを解析"""
    try:
        listings_data = []
        
        # Inventory API が返すのは JSON 形式
        if 'inventoryItems' in inventory_json:
            inventory_items = inventory_json['inventoryItems']
            
            for item in inventory_items:
                listing_info = {
                    'sku': item.get('sku', 'N/A'),
                    'title': item.get('product', {}).get('title', 'N/A'),
                    'category': item.get('product', {}).get('aspects', {}).get('Brand', ['N/A'])[0] if item.get('product', {}).get('aspects', {}).get('Brand') else 'N/A',
                    'price': float(item.get('offers', [{}])[0].get('price', {}).get('value', 0)) if item.get('offers') and item.get('offers')[0].get('price') else 0,
                    'quantity': int(item.get('availability', {}).get('shipToLocationAvailability', {}).get('quantity', 0)),
                    'condition': item.get('condition', 'N/A'),
                    'listing_status': 'Active' if item.get('availability', {}).get('shipToLocationAvailability', {}).get('quantity', 0) > 0 else 'Out of Stock'
                }
                listings_data.append(listing_info)
        
        return listings_data
    except Exception as e:
        print(f"Inventory データの解析に失敗: {e}")
        return []

@app.route('/generate-report', methods=['POST'])
def generate_report():
    if 'ebay_token' not in session:
        return {'error': 'Not authenticated'}, 401
    
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    
    if not access_token:
        return {'error': 'No access token available'}, 401
    
    try:
        # Inventory Task API を使用してレポートタスクを作成
        task_response = create_inventory_task(access_token)
        
        if task_response is None:
            # Inventory API 呼び出しが失敗した場合、バックアップとしてデモデータを返す
            listings_data = [
                {
                    'sku': 'DEMO-001',
                    'title': 'Sample Electronics Item',
                    'category': 'Electronics',
                    'price': 99.99,
                    'quantity': 10,
                    'condition': 'New',
                    'listing_status': 'Active'
                },
                {
                    'sku': 'DEMO-002', 
                    'title': 'Sample Fashion Item',
                    'category': 'Fashion',
                    'price': 49.99,
                    'quantity': 5,
                    'condition': 'New',
                    'listing_status': 'Active'
                }
            ]
        else:
            task_id = task_response.get('taskId')
            
            if not task_id:
                return {'error': 'タスクIDを取得できません'}, 500
            
            # 後続のステータス照会のためにタスクIDをセッションに保存
            session['inventory_task_id'] = task_id
            
            # タスク作成成功のメッセージを返す、実際のデータはタスク完了を待つ必要がある
            return {
                'status': 'task_created',
                'message': 'Inventoryレポートタスクが作成されました。後でステータスをご確認ください。',
                'task_id': task_id,
                'data': {
                    'task_status': 'IN_PROGRESS',
                    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'summary': 'eBay商品在庫レポートを生成中です。タスクの完了をお待ちください。'
                }
            }, 202
        
        # バックアップデータの処理ロジック
        session['listings_data'] = listings_data
        
        report_data = {
            'status': 'success',
            'message': 'レポートの生成が成功しました！（デモデータを使用）',
            'data': {
                'total_items': len(listings_data),
                'active_listings': len([item for item in listings_data if item['listing_status'] == 'Active']),
                'categories': list(set([item['category'] for item in listings_data])),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': f'{len(listings_data)}個の商品の詳細情報を正常に取得しました（デモデータ）'
            }
        }
        
        return report_data, 200
        
    except Exception as e:
        return {'error': f'レポート生成時にエラーが発生しました: {str(e)}'}, 500

@app.route('/check-feed-status', methods=['GET'])
def check_inventory_status():
    if 'ebay_token' not in session:
        return {'error': 'Not authenticated'}, 401
    
    if 'inventory_task_id' not in session:
        return {'error': 'Inventory タスクIDが見つかりません'}, 400
    
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    task_id = session['inventory_task_id']
    
    try:
        # タスクステータスを取得
        status_response = get_inventory_task_by_id(access_token, task_id)
        
        if status_response is None:
            return {'error': 'タスクステータスを取得できません'}, 500
        
        task_status = status_response.get('status')
        
        if task_status == 'COMPLETED':
            # タスク完了、結果をダウンロード
            inventory_data = download_inventory_result(access_token, task_id)
            
            if inventory_data:
                # Inventory データを解析
                listings_data = parse_inventory_data(inventory_data)
                
                # データをセッションに保存
                session['listings_data'] = listings_data
                
                return {
                    'status': 'success',
                    'message': 'Inventoryレポートが完了しました！',
                    'data': {
                        'total_items': len(listings_data),
                        'active_listings': len([item for item in listings_data if item['listing_status'] == 'Active']),
                        'categories': list(set([item['category'] for item in listings_data])),
                        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'summary': f'{len(listings_data)}個の商品の詳細情報を正常に取得しました'
                    }
                }, 200
            else:
                return {'error': 'Inventory結果をダウンロードできません'}, 500
        
        elif task_status == 'FAILED':
            return {'error': f'Inventoryタスクが失敗しました: {status_response.get("message", "不明なエラー")}'}, 500
        
        else:
            # タスクはまだ実行中
            return {
                'status': 'in_progress',
                'message': f'タスクステータス: {task_status}',
                'task_status': task_status
            }, 202
    
    except Exception as e:
        return {'error': f'タスクステータスの確認時にエラーが発生しました: {str(e)}'}, 500

# 新しいルート: 最近7日間のすべてのレポートを取得
@app.route('/get-recent-reports', methods=['GET'])
def get_recent_reports():
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    try:
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'アクセストークンが無効です'}, 401
            
        days = request.args.get('days', 7, type=int)
        
        recent_tasks = get_recent_inventory_tasks(access_token, days)
        
        if recent_tasks and 'tasks' in recent_tasks:
            tasks_list = []
            for task in recent_tasks['tasks']:
                task_info = {
                    'task_id': task.get('taskId'),
                    'status': task.get('status'),
                    'creation_date': task.get('creationDate'),
                    'completion_date': task.get('completionDate'),
                    'feed_type': task.get('feedType')
                }
                tasks_list.append(task_info)
            
            return {
                'status': 'success',
                'tasks': tasks_list,
                'total_count': len(tasks_list)
            }, 200
        else:
            return {
                'status': 'success',
                'tasks': [],
                'total_count': 0,
                'message': f'最近{days}日間にタスクが見つかりませんでした'
            }, 200
            
    except Exception as e:
        return {'error': f'最近のレポート取得時にエラーが発生しました: {str(e)}'}, 500

# 新しいルート: task_idによるタスクステータス照会
@app.route('/query-task-by-id', methods=['POST'])
def query_task_by_id():
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return {'error': 'task_idを提供してください'}, 400
        
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'アクセストークンが無効です'}, 401
            
        task_info = get_inventory_task_by_id(access_token, task_id)
        
        if task_info:
            return {
                'status': 'success',
                'task': {
                    'task_id': task_info.get('taskId'),
                    'status': task_info.get('status'),
                    'creation_date': task_info.get('creationDate'),
                    'completion_date': task_info.get('completionDate'),
                    'feed_type': task_info.get('feedType'),
                    'schema_version': task_info.get('schemaVersion'),
                    'detail_href': task_info.get('detailHref')
                }
            }, 200
        else:
            return {'error': f'タスクID: {task_id} のタスクが見つかりません'}, 404
            
    except Exception as e:
        return {'error': f'タスクの検索時にエラーが発生しました: {str(e)}'}, 500

# 新しいルート: タスク結果ファイルのダウンロード
@app.route('/download-task-result/<task_id>', methods=['GET'])
def download_task_result(task_id):
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    try:
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'アクセストークンが無効です'}, 401
        
        # 使用 eBay Feed API の getResultFile 端点
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/octet-stream',  # 下载文件
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        download_url = f'{EBAY_FEED_API_BASE_URL}/task/{task_id}/download_result_file'
        
        print(f"=== ダウンロードタスク結果ファイル ===")
        print(f"URL: {download_url}")
        print(f"Task ID: {task_id}")
        
        ssl_session = create_ssl_session()
        response = ssl_session.get(download_url, headers=headers)
        print(f"ダウンロードレスポンスステータスコード: {response.status_code}")
        print(f"ダウンロードレスポンスヘッダー: {response.headers}")
        print(f"ダウンロードレスポンスコンテンツ: {response.content}")
        
        if response.status_code == 200:
            # ファイル内容を取得
            file_content = response.content
            
            # レスポンスヘッダーから原始ファイル名とコンテンツタイプを取得
            content_disposition = response.headers.get('content-disposition', '')
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            # ファイル名を解析
            filename = None
            if 'filename' in content_disposition:
                # 提取文件名，处理可能的格式: filename = "name" 或 filename="name"
                import re
                filename_match = re.search(r'filename\s*=\s*["\']?([^"\';\s]+)["\']?', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
            
            # 如果没有找到文件名，使用默认名称
            if not filename:
                filename = f"ebay_inventory_report_{task_id}.zip"
            
            print(f"使用文件名: {filename}")
            print(f"内容类型: {content_type}")
            
            # 返回文件下载
            from flask import make_response
            download_response = make_response(file_content)
            download_response.headers['Content-Type'] = content_type
            download_response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return download_response
        else:
            print(f"下载失败响应内容: {response.text}")
            return {'error': f'下载失败: HTTP {response.status_code}'}, response.status_code
            
    except Exception as e:
        print(f"下载任务结果时出错: {str(e)}")
        return {'error': f'下载任务结果时出错: {str(e)}'}, 500

def get_item_details_trading_api(item_id, auth_token):
    """使用Trading API GetItem获取商品详细信息"""
    headers = {
        'X-EBAY-API-COMPATIBILITY-LEVEL': '1217',
        'X-EBAY-API-DEV-NAME': EBAY_APP_ID,
        'X-EBAY-API-CERT-NAME': EBAY_CERT_ID,
        'X-EBAY-API-CALL-NAME': 'GetItem',
        'X-EBAY-API-IAF-TOKEN': auth_token,
        'X-EBAY-API-SITEID': '0',  # US site
        'Content-Type': 'text/xml'
    }
    
    xml_request = f'''<?xml version="1.0" encoding="utf-8"?>
    <GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
        <ItemID>{item_id}</ItemID>
        <IncludeItemSpecifics>true</IncludeItemSpecifics>
        <DetailLevel>ItemReturnAttributes</DetailLevel>
    </GetItemRequest>'''
    
    try:
        ssl_session = create_ssl_session()
        response = ssl_session.post(EBAY_TRADING_API_URL, headers=headers, data=xml_request)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Trading API GetItem 调用失败 (ItemID: {item_id}): {e}")
        return None

def parse_get_item_response(xml_response):
    """解析GetItem响应XML，提取Item Specifics"""
    try:
        root = ET.fromstring(xml_response)
        
        # 定义命名空间
        ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
        
        item_data = {}
        
        # 基本信息
        item_data['ItemID'] = root.find('.//ebay:ItemID', ns).text if root.find('.//ebay:ItemID', ns) is not None else ''
        item_data['Title'] = root.find('.//ebay:Title', ns).text if root.find('.//ebay:Title', ns) is not None else ''
        item_data['SKU'] = root.find('.//ebay:SKU', ns).text if root.find('.//ebay:SKU', ns) is not None else ''
        
        # 价格信息
        current_price = root.find('.//ebay:CurrentPrice', ns)
        item_data['CurrentPrice'] = current_price.text if current_price is not None else ''
        item_data['Currency'] = current_price.get('currencyID') if current_price is not None else ''
        
        # 数量
        item_data['Quantity'] = root.find('.//ebay:Quantity', ns).text if root.find('.//ebay:Quantity', ns) is not None else ''
        
        # 类别
        primary_category = root.find('.//ebay:PrimaryCategory', ns)
        if primary_category is not None:
            item_data['CategoryID'] = primary_category.find('ebay:CategoryID', ns).text if primary_category.find('ebay:CategoryID', ns) is not None else ''
            item_data['CategoryName'] = primary_category.find('ebay:CategoryName', ns).text if primary_category.find('ebay:CategoryName', ns) is not None else ''
        
        
        # Item Specifics
        item_specifics = root.findall('.//ebay:ItemSpecifics/ebay:NameValueList', ns)
        specifics_dict = {}
        for specific in item_specifics:
            name = specific.find('ebay:Name', ns)
            value = specific.find('ebay:Value', ns)
            if name is not None and value is not None:
                specifics_dict[name.text] = value.text
        
        item_data['ItemSpecifics'] = specifics_dict
        
        return item_data
        
    except ET.ParseError as e:
        print(f"XML解析错误: {e}")
        return None
    except Exception as e:
        print(f"解析GetItem响应时出错: {e}")
        return None

def extract_item_ids_from_zip(zip_content):
    """从ZIP文件中提取ItemID列表"""
    try:
        item_ids = []
        
        print(f"ZIP文件大小: {len(zip_content)} bytes")
        
        with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
            # 获取ZIP中的所有文件
            all_files = zip_file.namelist()
            print(f"ZIP中的所有文件: {all_files}")
            
            # 获取ZIP中的XML文件
            xml_files = [f for f in all_files if f.endswith('.xml')]
            print(f"找到的XML文件: {xml_files}")
            
            if not xml_files:
                print("ZIP文件中未找到XML文件")
                return []
            
            # 读取第一个XML文件
            xml_content = zip_file.read(xml_files[0])
            print(f"XML文件大小: {len(xml_content)} bytes")
            
            # 解析XML
            root = ET.fromstring(xml_content)
            print(f"XML根元素: {root.tag}")
            
            # 打印XML结构的前几行用于调试
            xml_str = ET.tostring(root, encoding='unicode')
            print(f"XML内容前500字符: {xml_str[:500]}")
            
            # 定义命名空间
            ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
            
            # 查找所有ItemID - 使用正确的命名空间
            # 方法1: 使用命名空间查找SKUDetails
            sku_details = root.findall('.//ebay:SKUDetails', ns)
            print(f"找到 {len(sku_details)} 个SKUDetails元素")
            
            for sku_detail in sku_details:
                item_id_elem = sku_detail.find('ebay:ItemID', ns)
                if item_id_elem is not None and item_id_elem.text:
                    item_ids.append(item_id_elem.text)
                    print(f"找到ItemID: {item_id_elem.text}")
            
            # 方法2: 如果方法1没找到，直接查找所有ItemID元素
            if not item_ids:
                print("尝试直接查找ItemID元素...")
                all_item_ids = root.findall('.//ebay:ItemID', ns)
                print(f"找到 {len(all_item_ids)} 个ItemID元素")
                
                for item_id_elem in all_item_ids:
                    if item_id_elem.text:
                        item_ids.append(item_id_elem.text)
                        print(f"找到ItemID: {item_id_elem.text}")
        
        unique_item_ids = list(set(item_ids))  # 去重
        print(f"最终提取到 {len(unique_item_ids)} 个唯一ItemID: {unique_item_ids}")
        return unique_item_ids
        
    except Exception as e:
        print(f"从ZIP文件提取ItemID时出错: {e}")
        import traceback
        traceback.print_exc()
        return []

# 新增路由：生成增强的CSV报告（包含Item Specifics）
@app.route('/generate-enhanced-csv/<task_id>', methods=['GET', 'HEAD'])
def generate_enhanced_csv(task_id):
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    # HEAD请求：启动处理但不等待完成
    if request.method == 'HEAD':
        # 检查是否已经在处理中
        existing_progress = progress_manager.get_progress(task_id)
        if existing_progress and existing_progress.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return '', 202  # 已在处理中
        
        # 获取session数据传递给后台线程
        token_info = session.get('ebay_token')
        if not token_info:
            return {'error': 'ログインしていません'}, 401
        
        # 启动异步处理
        import threading
        def async_process():
            try:
                _process_enhanced_csv_async(task_id, token_info)
            except Exception as e:
                logger.error(f"异步处理错误: {e}")
                progress_manager.complete_task(task_id, success=False, message=f'エラー: {str(e)}')
        
        thread = threading.Thread(target=async_process)
        thread.daemon = True
        thread.start()
        
        return '', 202  # 处理已启动
    
    # GET请求：检查是否已完成并返回文件
    progress = progress_manager.get_progress(task_id)
    if progress and progress.status == TaskStatus.COMPLETED:
        # 文件已生成，返回下载
        import tempfile
        import os
        temp_file_path = os.path.join(tempfile.gettempdir(), f'enhanced_csv_{task_id}.csv')
        if os.path.exists(temp_file_path):
            filename = f'ebay_revise_template_{task_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return send_file(
                temp_file_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
    
    return {'error': 'ファイルが見つかりません'}, 404

def _process_enhanced_csv_async(task_id, token_info):
    """异步CSV生成处理逻辑"""
    # 启动进度跟踪
    progress_manager.start_task(task_id)
    
    access_token = token_info.get('access_token')
    
    if not access_token:
        progress_manager.complete_task(task_id, success=False, message='アクセストークンが無効です')
        return
    
    print(f"=== 拡張CSVレポートの生成 ===")
    print(f"Task ID: {task_id}")
    
    # 1. ZIPファイルをダウンロード
    progress_manager.update_progress(task_id, TaskStatus.DOWNLOADING, current_step=1, message='ZIPファイルをダウンロード中...')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/octet-stream',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    download_url = f'{EBAY_FEED_API_BASE_URL}/task/{task_id}/download_result_file'
    ssl_session = create_ssl_session()
    response = ssl_session.get(download_url, headers=headers)
    
    if response.status_code != 200:
        progress_manager.complete_task(task_id, success=False, message=f'レポートのダウンロードに失敗: HTTP {response.status_code}')
        return
    
    # 2. ZIPファイルからItemIDリストを抽出（最適化版）
    progress_manager.update_progress(task_id, TaskStatus.EXTRACTING, current_step=2, message='ItemIDを抽出中...')
    
    item_ids = xml_processor.extract_item_ids_from_zip(response.content)
    
    if not item_ids:
        progress_manager.complete_task(task_id, success=False, message='ZIPファイルからItemIDを抽出できませんでした')
        return
    
    logger.info(f"{len(item_ids)}個のItemIDが見つかりました")
    progress_manager.update_progress(task_id, TaskStatus.PROCESSING, current_step=3, total_items=len(item_ids), message=f'{len(item_ids)}個のアイテム詳細を取得中...')
    
    # 3. 並列処理でアイテム詳細を取得（最適化版）
    enhanced_data_raw = xml_processor.get_item_details_batch(item_ids, access_token, task_id)
    
    if not enhanced_data_raw:
        progress_manager.complete_task(task_id, success=False, message='商品の詳細情報を取得できませんでした')
        return
    
    # 4. eBayテンプレート形式用にデータを変換
    progress_manager.update_progress(task_id, TaskStatus.GENERATING, current_step=4, message='CSVファイルを生成中...')
    
    enhanced_data = []
    for item_data in enhanced_data_raw:
        item_specifics = item_data.get('ItemSpecifics', {})
        logger.info(f"ItemID {item_data.get('ItemID')} (USD通貨) の Item Specifics: {item_specifics}")
        
        # 基本データ構造
        row_data = {
            'ItemID': item_data.get('ItemID', ''),
            'Title': item_data.get('Title', ''),
            'SKU': item_data.get('SKU', ''),
            'CurrentPrice': item_data.get('CurrentPrice', ''),
            'Currency': item_data.get('Currency', ''),
            'Quantity': item_data.get('Quantity', ''),
            'CategoryID': item_data.get('CategoryID', ''),
            'CategoryName': item_data.get('CategoryName', '')
        }
        
        # Item Specificsを個別の列として追加
        for spec_name, spec_value in item_specifics.items():
            column_name = f"ItemSpecific_{spec_name}"
            row_data[column_name] = spec_value
        
        enhanced_data.append(row_data)
    
    # 4. eBayテンプレート形式のCSVを作成
    ebay_template_data = []
    
    for item in enhanced_data:
        # 基本的なeBayテンプレート行データ
        row = {
            'Action': 'Revise',
            'Category name': item.get('CategoryName', ''),
            'Item number': item.get('ItemID', ''),
            'Title': item.get('Title', ''),
            'Listing site': 'US',
            'Currency': item.get('Currency', 'USD'),
            'Start price': item.get('CurrentPrice', ''),
            'Buy It Now price': '',
            'Available quantity': item.get('Quantity', ''),
            'Relationship': '',
            'Relationship details': '',
            'Custom label (SKU)': item.get('SKU', '')
        }
        
        # Item SpecificsをC:形式で追加
        for key, value in item.items():
            if key.startswith('ItemSpecific_'):
                spec_name = key.replace('ItemSpecific_', '')
                column_name = f"C:{spec_name}"
                row[column_name] = value
        
        ebay_template_data.append(row)
    
    # CSVファイルを一時ファイルとして保存
    import tempfile
    import os
    
    # CSVコンテンツを作成
    output = BytesIO()
    
    # INFOヘッダーを書き込み
    info_header = "#INFO,Version=1.0.0,Template= eBay-active-revise-price-quantity-download_US\n"
    output.write(info_header.encode('utf-8-sig'))
    
    # DataFrameを作成しCSVデータを書き込み
    df = pd.DataFrame(ebay_template_data)
    csv_content = df.to_csv(index=False, encoding='utf-8')
    output.write(csv_content.encode('utf-8'))
    
    # 一時ファイルに保存
    temp_file_path = os.path.join(tempfile.gettempdir(), f'enhanced_csv_{task_id}.csv')
    with open(temp_file_path, 'wb') as f:
        f.write(output.getvalue())
    
    logger.info(f"拡張CSVの生成完了、成功: {len(enhanced_data)}件")
    progress_manager.complete_task(task_id, success=True, message=f'CSV生成完了 - {len(enhanced_data)}件のアイテム')

@app.route('/export-csv')
def export_csv():
    if 'ebay_token' not in session:
        return redirect(url_for('index'))
    
    if 'listings_data' not in session:
        return {'error': 'エクスポートするデータがありません。まずレポートを生成してください'}, 400
    
    try:
        # DataFrameを作成
        df = pd.DataFrame(session['listings_data'])
        
        # CSVファイルを作成
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')  # utf-8-sigは日本語をサポート
        output.seek(0)
        
        filename = f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return {'error': f'CSVエクスポート時にエラーが発生しました: {str(e)}'}, 500

@app.route('/export-excel')
def export_excel():
    if 'ebay_token' not in session:
        return redirect(url_for('index'))
    
    if 'listings_data' not in session:
        return {'error': 'エクスポートするデータがありません。まずレポートを生成してください'}, 400
    
    try:
        # DataFrameを作成
        df = pd.DataFrame(session['listings_data'])
        
        # Excelファイルを作成
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='eBay Listings', index=False)
            
            # ワークシートを取得して列幅を設定
            worksheet = writer.sheets['eBay Listings']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        filename = f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return {'error': f'Excelエクスポート時にエラーが発生しました: {str(e)}'}, 500

# 新增路由：SSE进度推送
@app.route('/progress/<task_id>')
def progress_stream(task_id):
    """Server-Sent Events进度推送"""
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    def generate():
        while True:
            progress = progress_manager.get_progress(task_id)
            if progress:
                # 计算经过时间
                elapsed_time = time.time() - progress.start_time
                
                data = {
                    'task_id': progress.task_id,
                    'status': progress.status.value,
                    'current_step': progress.current_step,
                    'total_steps': progress.total_steps,
                    'current_item': progress.current_item,
                    'total_items': progress.total_items,
                    'progress_percentage': progress.progress_percentage,
                    'message': progress.message,
                    'elapsed_time': round(elapsed_time, 1)
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
                # 如果任务完成或失败，结束推送
                if progress.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    break
            else:
                # 任务不存在
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break
            
            time.sleep(1)  # 每秒推送一次
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# 新增路由：轮询方式获取进度状态（SSE备用方案）
@app.route('/progress-poll/<task_id>')
def progress_poll(task_id):
    """轮询方式获取任务进度状态"""
    if 'ebay_token' not in session:
        return {'error': 'ログインしていません'}, 401
    
    progress = progress_manager.get_progress(task_id)
    if progress:
        elapsed_time = time.time() - progress.start_time
        
        return {
            'status': 'success',
            'data': {
                'task_id': progress.task_id,
                'status': progress.status.value,
                'current_step': progress.current_step,
                'total_steps': progress.total_steps,
                'current_item': progress.current_item,
                'total_items': progress.total_items,
                'progress_percentage': progress.progress_percentage,
                'message': progress.message,
                'elapsed_time': round(elapsed_time, 1)
            }
        }, 200
    else:
        return {'error': 'Task not found'}, 404

if __name__ == '__main__':
    # Ensure the callback URL is correctly set for local testing
    print("--- Local Development Server ---")
    print("Ensure your eBay app's Redirect URI is set to: http://127.0.0.1:8080/callback")
    print("--------------------------------")
    app.run(debug=True, host='0.0.0.0', port=8080)
