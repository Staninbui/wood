import os
import requests
import base64
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlencode, parse_qs
from flask import Flask, redirect, request, session, url_for, render_template, send_file
from io import BytesIO

app = Flask(__name__)
# A secret key is needed for session management
app.secret_key = os.urandom(24)

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
    # 添加调试信息
    print(f"Callback received with args: {request.args}")
    print(f"Full request URL: {request.url}")
    
    auth_code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # 如果有错误参数，显示错误信息
    if error:
        return f"eBay OAuth Error: {error} - {error_description}", 400
    
    if not auth_code:
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
        'code': auth_code,
        'redirect_uri': EBAY_RU_NAME
    }

    try:
        response = requests.post(EBAY_TOKEN_URL, headers=headers, data=data)
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
    """创建 eBay Inventory Task 获取 active listings"""
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
    
    print(f"=== Inventory Task API 调试信息 ===")
    print(f"URL: {EBAY_INVENTORY_REPORT_URL}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(EBAY_INVENTORY_REPORT_URL, headers=headers, json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        
        # 202 表示任务创建成功
        if response.status_code == 202:
            # 从 Location 头部提取 task_id
            location = response.headers.get('Location', '')
            print(f"Location 头部: {location}")
            
            if location:
                # 从 URL 中提取 task_id (例如: task-20-23232459833347 中的 task-20)
                task_id = location.split('/')[-1]
                print(f"提取的 task_id: {task_id}")
                
                return {
                    'taskId': task_id,
                    'status': 'CREATED',
                    'location': location
                }
            else:
                print("未找到 Location 头部")
                return None
        else:
            response.raise_for_status()
            return response.json()
            
    except requests.RequestException as e:
        print(f"创建 Inventory 任务失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误响应状态码: {e.response.status_code}")
            print(f"错误响应内容: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"错误 JSON: {error_json}")
            except:
                pass
        return None

def get_inventory_task_status(access_token, task_id):
    """获取 Inventory 任务状态"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    try:
        response = requests.get(f'{EBAY_INVENTORY_REPORT_DOWNLOAD_URL.format(task_id=task_id)}', headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"获取 Inventory 任务状态失败: {e}")
        return None

def get_inventory_task_by_id(access_token, task_id):
    """根据 task_id 获取单个 Inventory 任务状态"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    # 使用 GET /inventory_task/{task_id} 端点
    url = f'{EBAY_INVENTORY_REPORT_URL}/{task_id}'
    
    try:
        response = requests.get(url, headers=headers)
        print(f"单个任务状态检查响应状态码: {response.status_code}")
        print(f"单个任务状态检查响应内容: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"获取单个 Inventory 任务状态失败: {e}")
        return None

def get_recent_inventory_tasks(access_token, days=7):
    """获取最近指定天数内的所有 Inventory 任务"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    # 计算日期范围
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    date_range = f"{start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')}..{end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
    
    params = {
        'feed_type': 'LMS_ACTIVE_INVENTORY_REPORT',
        'date_range': date_range,
        'limit': 50,
        'offset': 0
    }
    
    try:
        response = requests.get(EBAY_INVENTORY_REPORT_URL, headers=headers, params=params)
        print(f"最近任务列表响应状态码: {response.status_code}")
        print(f"最近任务列表响应内容: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"获取最近 Inventory 任务列表失败: {e}")
        return None

def download_inventory_result(access_token, task_id):
    """下载 Inventory 任务结果"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
    }
    
    download_url = EBAY_INVENTORY_REPORT_DOWNLOAD_URL.format(task_id=task_id)
    print(f"=== Inventory Download API 调试信息 ===")
    print(f"URL: {download_url}")
    print(f"Task ID: {task_id}")
    
    try:
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
        return response.json()  # Inventory API 通常返回 JSON 格式
    except requests.RequestException as e:
        print(f"下载 Inventory 结果失败: {e}")
        return None

def parse_inventory_data(inventory_json):
    """解析 Inventory API 返回的 JSON 数据"""
    try:
        listings_data = []
        
        # Inventory API 返回的是 JSON 格式
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
        print(f"解析 Inventory 数据失败: {e}")
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
        # 使用 Inventory Task API 创建报告任务
        task_response = create_inventory_task(access_token)
        
        if task_response is None:
            # 如果 Inventory API 调用失败，返回模拟数据作为备用
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
                return {'error': '无法获取任务 ID'}, 500
            
            # 存储任务 ID 到 session，以便后续查询状态
            session['inventory_task_id'] = task_id
            
            # 返回任务创建成功的消息，实际数据需要等待任务完成
            return {
                'status': 'task_created',
                'message': 'Inventory 报告任务已创建，请稍后查看状态',
                'task_id': task_id,
                'data': {
                    'task_status': 'IN_PROGRESS',
                    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'summary': '正在生成 eBay 商品库存报告，请等待任务完成'
                }
            }, 202
        
        # 备用数据的处理逻辑
        session['listings_data'] = listings_data
        
        report_data = {
            'status': 'success',
            'message': '报告生成成功！（使用演示数据）',
            'data': {
                'total_items': len(listings_data),
                'active_listings': len([item for item in listings_data if item['listing_status'] == 'Active']),
                'categories': list(set([item['category'] for item in listings_data])),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': f'成功获取了 {len(listings_data)} 个商品的详细信息（演示数据）'
            }
        }
        
        return report_data, 200
        
    except Exception as e:
        return {'error': f'生成报告时出错: {str(e)}'}, 500

@app.route('/check-feed-status', methods=['GET'])
def check_inventory_status():
    if 'ebay_token' not in session:
        return {'error': 'Not authenticated'}, 401
    
    if 'inventory_task_id' not in session:
        return {'error': '没有找到 Inventory 任务 ID'}, 400
    
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    task_id = session['inventory_task_id']
    
    try:
        # 获取任务状态
        status_response = get_inventory_task_by_id(access_token, task_id)
        
        if status_response is None:
            return {'error': '无法获取任务状态'}, 500
        
        task_status = status_response.get('status')
        
        if task_status == 'COMPLETED':
            # 任务完成，下载结果
            inventory_data = download_inventory_result(access_token, task_id)
            
            if inventory_data:
                # 解析 Inventory 数据
                listings_data = parse_inventory_data(inventory_data)
                
                # 存储数据到 session
                session['listings_data'] = listings_data
                
                return {
                    'status': 'success',
                    'message': 'Inventory 报告已完成！',
                    'data': {
                        'total_items': len(listings_data),
                        'active_listings': len([item for item in listings_data if item['listing_status'] == 'Active']),
                        'categories': list(set([item['category'] for item in listings_data])),
                        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'summary': f'成功获取了 {len(listings_data)} 个商品的详细信息'
                    }
                }, 200
            else:
                return {'error': '无法下载 Inventory 结果'}, 500
        
        elif task_status == 'FAILED':
            return {'error': f'Inventory 任务失败: {status_response.get("message", "未知错误")}'}, 500
        
        else:
            # 任务仍在进行中
            return {
                'status': 'in_progress',
                'message': f'任务状态: {task_status}',
                'task_status': task_status
            }, 202
    
    except Exception as e:
        return {'error': f'检查任务状态时出错: {str(e)}'}, 500

# 新增路由：获取最近7天内的所有报告
@app.route('/get-recent-reports', methods=['GET'])
def get_recent_reports():
    if 'ebay_token' not in session:
        return {'error': '未登录'}, 401
    
    try:
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'Access token 无效'}, 401
            
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
                'message': f'最近 {days} 天内没有找到任务'
            }, 200
            
    except Exception as e:
        return {'error': f'获取最近报告时出错: {str(e)}'}, 500

# 新增路由：通过 task_id 查询任务状态
@app.route('/query-task-by-id', methods=['POST'])
def query_task_by_id():
    if 'ebay_token' not in session:
        return {'error': '未登录'}, 401
    
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return {'error': '请提供 task_id'}, 400
        
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'Access token 无效'}, 401
            
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
            return {'error': f'未找到 task_id: {task_id} 的任务'}, 404
            
    except Exception as e:
        return {'error': f'查询任务时出错: {str(e)}'}, 500

# 新增路由：下载任务结果文件
@app.route('/download-task-result/<task_id>', methods=['GET'])
def download_task_result(task_id):
    if 'ebay_token' not in session:
        return {'error': '未登录'}, 401
    
    try:
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'Access token 无效'}, 401
        
        # 使用 eBay Feed API 的 getResultFile 端点
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/octet-stream',  # 下载文件
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        download_url = f'{EBAY_FEED_API_BASE_URL}/task/{task_id}/download_result_file'
        
        print(f"=== 下载任务结果文件 ===")
        print(f"URL: {download_url}")
        print(f"Task ID: {task_id}")
        
        response = requests.get(download_url, headers=headers)
        print(f"下载响应状态码: {response.status_code}")
        print(f"下载响应头: {response.headers}")
        print(f"下载响应内容: {response.content}")
        
        if response.status_code == 200:
            # 获取文件内容
            file_content = response.content
            
            # 从响应头获取原始文件名和内容类型
            content_disposition = response.headers.get('content-disposition', '')
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            # 解析文件名
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
        response = requests.post(EBAY_TRADING_API_URL, headers=headers, data=xml_request)
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
@app.route('/generate-enhanced-csv/<task_id>', methods=['GET'])
def generate_enhanced_csv(task_id):
    if 'ebay_token' not in session:
        return {'error': '未登录'}, 401
    
    try:
        token_info = session['ebay_token']
        access_token = token_info.get('access_token')
        
        if not access_token:
            return {'error': 'Access token 无效'}, 401
        
        print(f"=== 生成增强CSV报告 ===")
        print(f"Task ID: {task_id}")
        
        # 1. 下载ZIP文件
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/octet-stream',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        download_url = f'{EBAY_FEED_API_BASE_URL}/task/{task_id}/download_result_file'
        response = requests.get(download_url, headers=headers)
        
        if response.status_code != 200:
            return {'error': f'下载报告失败: HTTP {response.status_code}'}, response.status_code
        
        # 2. 从ZIP文件提取ItemID列表
        item_ids = extract_item_ids_from_zip(response.content)
        
        if not item_ids:
            return {'error': '未能从报告中提取到ItemID'}, 400
        
        print(f"找到 {len(item_ids)} 个ItemID")
        
        # 3. 逐个调用Trading API获取详细信息
        enhanced_data = []
        failed_items = []
        
        for i, item_id in enumerate(item_ids):
            print(f"处理 ItemID {item_id} ({i+1}/{len(item_ids)})")
            
            # 调用Trading API GetItem
            xml_response = get_item_details_trading_api(item_id, access_token)
            
            if xml_response:
                # 解析响应
                item_data = parse_get_item_response(xml_response)
                
                if item_data:
                    # 过滤：只处理USD货币的商品
                    currency = item_data.get('Currency', '')
                    if currency != 'USD':
                        print(f"跳过非USD商品 ItemID {item_id}, 货币: {currency}")
                        continue
                    
                    # 调试：打印Item Specifics信息
                    item_specifics = item_data.get('ItemSpecifics', {})
                    print(f"ItemID {item_id} (USD货币) 的 Item Specifics: {item_specifics}")
                    
                    # 将Item Specifics展开为单独的列
                    row_data = {
                        'ItemID': item_data.get('ItemID', ''),
                        'Title': item_data.get('Title', ''),
                        'SKU': item_data.get('SKU', ''),
                        'CurrentPrice': item_data.get('CurrentPrice', ''),
                        'Currency': currency,
                        'Quantity': item_data.get('Quantity', ''),
                        'CategoryID': item_data.get('CategoryID', ''),
                        'CategoryName': item_data.get('CategoryName', '')
                    }
                    
                    # 添加Item Specifics作为单独的列
                    for spec_name, spec_value in item_specifics.items():
                        # 使用前缀避免列名冲突
                        column_name = f"ItemSpecific_{spec_name}"
                        row_data[column_name] = spec_value
                    
                    enhanced_data.append(row_data)
                else:
                    failed_items.append(item_id)
            else:
                failed_items.append(item_id)
        
        if not enhanced_data:
            return {'error': '未能获取到任何商品详细信息'}, 400
        
        # 4. 创建eBay模板格式的CSV
        ebay_template_data = []
        
        for item in enhanced_data:
            # 基本eBay模板行数据
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
            
            # 添加Item Specifics为C:格式
            # 从enhanced_data中提取ItemSpecific_前缀的字段
            for key, value in item.items():
                if key.startswith('ItemSpecific_'):
                    # 移除ItemSpecific_前缀，添加C:前缀
                    spec_name = key.replace('ItemSpecific_', '')
                    column_name = f"C:{spec_name}"
                    row[column_name] = value
            
            ebay_template_data.append(row)
        
        # 创建CSV内容
        output = BytesIO()
        
        # 写入INFO头部 - 作为单行三列
        info_header = "#INFO,Version=1.0.0,Template= eBay-active-revise-price-quantity-download_US\n"
        output.write(info_header.encode('utf-8-sig'))
        
        # 创建DataFrame并写入CSV数据
        df = pd.DataFrame(ebay_template_data)
        csv_content = df.to_csv(index=False, encoding='utf-8')
        output.write(csv_content.encode('utf-8'))
        
        output.seek(0)
        
        filename = f"ebay_revise_template_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        print(f"生成增强CSV完成，成功: {len(enhanced_data)}, 失败: {len(failed_items)}")
        if failed_items:
            print(f"失败的ItemID: {failed_items}")
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"生成增强CSV时出错: {str(e)}")
        return {'error': f'生成增强CSV时出错: {str(e)}'}, 500

@app.route('/export-csv')
def export_csv():
    if 'ebay_token' not in session:
        return redirect(url_for('index'))
    
    if 'listings_data' not in session:
        return {'error': '没有可导出的数据，请先生成报告'}, 400
    
    try:
        # 创建 DataFrame
        df = pd.DataFrame(session['listings_data'])
        
        # 创建 CSV 文件
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')  # utf-8-sig 支持中文
        output.seek(0)
        
        filename = f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return {'error': f'导出 CSV 时出错: {str(e)}'}, 500

@app.route('/export-excel')
def export_excel():
    if 'ebay_token' not in session:
        return redirect(url_for('index'))
    
    if 'listings_data' not in session:
        return {'error': '没有可导出的数据，请先生成报告'}, 400
    
    try:
        # 创建 DataFrame
        df = pd.DataFrame(session['listings_data'])
        
        # 创建 Excel 文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='eBay Listings', index=False)
            
            # 获取工作表并设置列宽
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
        return {'error': f'导出 Excel 时出错: {str(e)}'}, 500

if __name__ == '__main__':
    # Ensure the callback URL is correctly set for local testing
    print("--- Local Development Server ---")
    print("Ensure your eBay app's Redirect URI is set to: http://127.0.0.1:8080/callback")
    print("--------------------------------")
    app.run(debug=True, host='0.0.0.0', port=8080)
