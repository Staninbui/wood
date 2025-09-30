"""
eBay API服务层
"""
import os
import requests
import base64
import logging
from datetime import datetime
from typing import Dict, Optional, List
from flask import current_app
from app.utils.ssl_utils import create_ssl_session

logger = logging.getLogger(__name__)


class EbayService:
    """eBay API服务类"""
    
    def __init__(self, config=None):
        self.ssl_session = create_ssl_session()
        if config:
            self.config = config
        else:
            from flask import current_app
            self.config = current_app.config
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict]:
        """交换授权码获取访问令牌"""
        app_id = self.config['EBAY_APP_ID']
        cert_id = self.config['EBAY_CERT_ID']
        token_url = self.config['EBAY_TOKEN_URL']
        
        credentials = f"{app_id}:{cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        try:
            response = self.ssl_session.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return None
    
    def create_inventory_task(self, access_token: str) -> Optional[Dict]:
        """创建库存报告任务"""
        inventory_report_url = f"{self.config['EBAY_FEED_API_BASE_URL']}/inventory_task"
        
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
        
        try:
            response = self.ssl_session.post(inventory_report_url, headers=headers, json=payload)
            logger.info(f"Inventory task creation response: {response.status_code}")
            
            if response.status_code == 202:
                location = response.headers.get('Location', '')
                if location:
                    task_id = location.split('/')[-1]
                    return {
                        'taskId': task_id,
                        'status': 'CREATED',
                        'location': location
                    }
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Inventory task creation failed: {e}")
            return None
    
    def get_inventory_task_status(self, access_token: str, task_id: str) -> Optional[Dict]:
        """获取库存任务状态"""
        inventory_report_url = f"{self.config['EBAY_FEED_API_BASE_URL']}/inventory_task"
        url = f'{inventory_report_url}/{task_id}'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        try:
            response = self.ssl_session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Task status retrieval failed: {e}")
            return None
    
    def get_recent_inventory_tasks(self, access_token: str, days: int = 7) -> Optional[Dict]:
        """获取最近的库存任务列表"""
        inventory_report_url = f"{self.config['EBAY_FEED_API_BASE_URL']}/inventory_task"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        date_from = start_date.strftime('%Y-%m-%dT%H:%M:%S') + f'.{start_date.microsecond // 1000:03d}Z'
        date_to = end_date.strftime('%Y-%m-%dT%H:%M:%S') + f'.{end_date.microsecond // 1000:03d}Z'
        
        params = {
            'date_range': f'{date_from}..{date_to}',
            'feed_type': 'LMS_ACTIVE_INVENTORY_REPORT',
            'limit': '200'
        }
        
        try:
            response = self.ssl_session.get(inventory_report_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Recent tasks retrieval failed: {e}")
            return None
    
    def download_task_result(self, access_token: str, task_id: str) -> Optional[bytes]:
        """下载任务结果文件"""
        feed_api_base_url = self.config['EBAY_FEED_API_BASE_URL']
        download_url = f'{feed_api_base_url}/task/{task_id}/download_result_file'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/octet-stream',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        try:
            response = self.ssl_session.get(download_url, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Task result download failed: {e}")
            return None
    
    def get_item_details_trading_api(self, item_id: str, auth_token: str) -> Optional[str]:
        """使用Trading API获取商品详情"""
        trading_api_url = self.config['EBAY_TRADING_API_URL']
        app_id = self.config['EBAY_APP_ID']
        cert_id = self.config['EBAY_CERT_ID']
        
        xml_request = f'''<?xml version="1.0" encoding="utf-8"?>
        <GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <ItemID>{item_id}</ItemID>
            <IncludeItemSpecifics>true</IncludeItemSpecifics>
            <DetailLevel>ItemReturnAttributes</DetailLevel>
        </GetItemRequest>'''
        
        headers = {
            'X-EBAY-API-COMPATIBILITY-LEVEL': '1217',
            'X-EBAY-API-DEV-NAME': app_id,
            'X-EBAY-API-CERT-NAME': cert_id,
            'X-EBAY-API-CALL-NAME': 'GetItem',
            'X-EBAY-API-IAF-TOKEN': auth_token,
            'X-EBAY-API-SITEID': '0',
            'Content-Type': 'text/xml'
        }
        
        try:
            response = self.ssl_session.post(trading_api_url, headers=headers, data=xml_request)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Trading API GetItem failed for ItemID {item_id}: {e}")
            return None
    
    def build_oauth_url(self, redirect_uri: str) -> str:
        """构建OAuth授权URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.config['EBAY_APP_ID'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.config['EBAY_SCOPES'])
        }
        
        oauth_base_url = self.config['EBAY_OAUTH_BASE_URL']
        return f"{oauth_base_url}?{urlencode(params)}"
