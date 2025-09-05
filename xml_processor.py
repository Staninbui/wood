import os
import xml.etree.ElementTree as ET
import zipfile
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import List, Dict, Optional
import time
import ssl
import urllib3
from urllib3.util import ssl_

# SSL configuration to prevent recursion errors (same as main app)
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey patch urllib3 to avoid SSL context creation issues
def patched_create_urllib3_context(ssl_version=None, cert_reqs=None, options=None, ciphers=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

ssl_.create_urllib3_context = patched_create_urllib3_context

logger = logging.getLogger(__name__)

class XMLProcessor:
    """XML処理を最適化するクラス"""
    
    def __init__(self, max_workers: int = 4, timeout: int = 300):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = self._create_ssl_session()
    
    def _create_ssl_session(self):
        """Create SSL-safe session to prevent recursion errors"""
        session = requests.Session()
        session.verify = False
        
        # Use a custom adapter to bypass SSL issues
        from requests.adapters import HTTPAdapter
        
        class NoSSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                kwargs['ssl_context'] = ssl.create_default_context()
                kwargs['ssl_context'].check_hostname = False
                kwargs['ssl_context'].verify_mode = ssl.CERT_NONE
                return super().init_poolmanager(*args, **kwargs)
        
        session.mount('https://', NoSSLAdapter())
        session.mount('http://', NoSSLAdapter())
        return session
    
    def extract_item_ids_from_zip(self, zip_content: bytes) -> List[str]:
        """ZIPファイルからItemIDリストを抽出（最適化版）"""
        try:
            item_ids = []
            
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
                xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                
                if not xml_files:
                    logger.warning("ZIP文件中未找到XML文件")
                    return []
                
                # 最初のXMLファイルを読み込み
                xml_content = zip_file.read(xml_files[0])
                
                # XMLパーサーの最適化設定
                parser = ET.XMLParser(encoding='utf-8')
                root = ET.fromstring(xml_content, parser=parser)
                
                # 名前空間の定義
                ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
                
                # ItemIDを効率的に抽出
                for sku_detail in root.findall('.//ebay:SKUDetails', ns):
                    item_id_elem = sku_detail.find('ebay:ItemID', ns)
                    if item_id_elem is not None and item_id_elem.text:
                        item_ids.append(item_id_elem.text)
                
                # フォールバック: 直接ItemIDを検索
                if not item_ids:
                    for item_id_elem in root.findall('.//ebay:ItemID', ns):
                        if item_id_elem.text:
                            item_ids.append(item_id_elem.text)
            
            unique_item_ids = list(set(item_ids))
            logger.info(f"抽出された一意のItemID数: {len(unique_item_ids)}")
            return unique_item_ids
            
        except Exception as e:
            logger.error(f"ZIP文件からのItemID抽出エラー: {e}")
            return []
    
    def get_item_details_batch(self, item_ids: List[str], access_token: str) -> List[Dict]:
        """バッチでアイテム詳細を取得（並列処理）"""
        results = []
        failed_items = []
        
        def fetch_single_item(item_id: str) -> Optional[Dict]:
            """単一アイテムの詳細を取得"""
            try:
                xml_response = self._get_item_details_trading_api(item_id, access_token)
                if xml_response:
                    return self._parse_get_item_response(xml_response)
                return None
            except Exception as e:
                logger.error(f"ItemID {item_id} の取得エラー: {e}")
                return None
        
        # 並列処理でアイテム詳細を取得
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # タスクを送信
            future_to_item_id = {
                executor.submit(fetch_single_item, item_id): item_id 
                for item_id in item_ids
            }
            
            # 結果を収集
            for future in as_completed(future_to_item_id, timeout=self.timeout):
                item_id = future_to_item_id[future]
                try:
                    result = future.result()
                    if result:
                        # USD通貨のみフィルタリング
                        if result.get('Currency') == 'USD':
                            results.append(result)
                            logger.info(f"ItemID {item_id} (USD) 処理完了")
                        else:
                            logger.info(f"ItemID {item_id} スキップ (通貨: {result.get('Currency', 'N/A')})")
                    else:
                        failed_items.append(item_id)
                except Exception as e:
                    logger.error(f"ItemID {item_id} 処理エラー: {e}")
                    failed_items.append(item_id)
        
        logger.info(f"処理完了 - 成功: {len(results)}, 失敗: {len(failed_items)}")
        return results
    
    def _get_item_details_trading_api(self, item_id: str, auth_token: str) -> Optional[str]:
        """Trading API GetItemを呼び出し（セッション使用）"""
        headers = {
            'X-EBAY-API-COMPATIBILITY-LEVEL': '1217',
            'X-EBAY-API-DEV-NAME': os.environ.get('EBAY_APP_ID'),
            'X-EBAY-API-CERT-NAME': os.environ.get('EBAY_CERT_ID'),
            'X-EBAY-API-CALL-NAME': 'GetItem',
            'X-EBAY-API-IAF-TOKEN': auth_token,
            'X-EBAY-API-SITEID': '0',
            'Content-Type': 'text/xml'
        }
        
        xml_request = f'''<?xml version="1.0" encoding="utf-8"?>
        <GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <ItemID>{item_id}</ItemID>
            <IncludeItemSpecifics>true</IncludeItemSpecifics>
            <DetailLevel>ItemReturnAttributes</DetailLevel>
        </GetItemRequest>'''
        
        try:
            response = self.session.post(
                'https://api.ebay.com/ws/api.dll',
                headers=headers,
                data=xml_request,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Trading API GetItem 呼び出し失敗 (ItemID: {item_id}): {e}")
            return None
    
    def _parse_get_item_response(self, xml_response: str) -> Optional[Dict]:
        """GetItem応答XMLを解析（最適化版）"""
        try:
            # XMLパーサーの最適化
            parser = ET.XMLParser(encoding='utf-8')
            root = ET.fromstring(xml_response, parser=parser)
            
            ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
            
            # 基本情報を効率的に抽出
            item_data = {}
            
            # 必要な要素のみ抽出
            elements_to_extract = {
                'ItemID': './/ebay:ItemID',
                'Title': './/ebay:Title',
                'SKU': './/ebay:SKU',
                'Quantity': './/ebay:Quantity'
            }
            
            for key, xpath in elements_to_extract.items():
                elem = root.find(xpath, ns)
                item_data[key] = elem.text if elem is not None else ''
            
            # 価格情報
            current_price = root.find('.//ebay:CurrentPrice', ns)
            if current_price is not None:
                item_data['CurrentPrice'] = current_price.text
                item_data['Currency'] = current_price.get('currencyID', '')
            else:
                item_data['CurrentPrice'] = ''
                item_data['Currency'] = ''
            
            # カテゴリ情報
            primary_category = root.find('.//ebay:PrimaryCategory', ns)
            if primary_category is not None:
                category_id = primary_category.find('ebay:CategoryID', ns)
                category_name = primary_category.find('ebay:CategoryName', ns)
                item_data['CategoryID'] = category_id.text if category_id is not None else ''
                item_data['CategoryName'] = category_name.text if category_name is not None else ''
            
            # Item Specifics（最適化）
            specifics_dict = {}
            for specific in root.findall('.//ebay:ItemSpecifics/ebay:NameValueList', ns):
                name_elem = specific.find('ebay:Name', ns)
                value_elem = specific.find('ebay:Value', ns)
                if name_elem is not None and value_elem is not None:
                    specifics_dict[name_elem.text] = value_elem.text
            
            item_data['ItemSpecifics'] = specifics_dict
            
            return item_data
            
        except ET.ParseError as e:
            logger.error(f"XML解析エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"GetItem応答解析エラー: {e}")
            return None
    
    def __del__(self):
        """セッションのクリーンアップ"""
        if hasattr(self, 'session'):
            self.session.close()
