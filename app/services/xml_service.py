"""
XML处理服务层
"""
import os
import xml.etree.ElementTree as ET
import zipfile
import subprocess
import logging
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import time
from flask import current_app

logger = logging.getLogger(__name__)


class XMLService:
    """XML处理服务类"""
    
    def __init__(self, config=None):
        if config:
            self.max_workers = config.get('MAX_WORKERS', 4)
            self.timeout = config.get('TASK_TIMEOUT', 300)
            self.config = config
        else:
            self.max_workers = current_app.config.get('MAX_WORKERS', 4)
            self.timeout = current_app.config.get('TASK_TIMEOUT', 300)
            self.config = current_app.config
    
    def extract_item_ids_from_zip(self, zip_content: bytes) -> List[str]:
        """从ZIP文件中提取ItemID列表"""
        try:
            item_ids = []
            
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
                xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                
                if not xml_files:
                    logger.warning("ZIP文件中未找到XML文件")
                    return []
                
                # 读取第一个XML文件
                xml_content = zip_file.read(xml_files[0])
                
                # 解析XML
                parser = ET.XMLParser(encoding='utf-8')
                root = ET.fromstring(xml_content, parser=parser)
                
                # 定义命名空间
                ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
                
                # 方法1: 查找SKUDetails中的ItemID
                for sku_detail in root.findall('.//ebay:SKUDetails', ns):
                    item_id_elem = sku_detail.find('ebay:ItemID', ns)
                    if item_id_elem is not None and item_id_elem.text:
                        item_ids.append(item_id_elem.text)
                
                # 方法2: 如果方法1没找到，直接查找所有ItemID元素
                if not item_ids:
                    for item_id_elem in root.findall('.//ebay:ItemID', ns):
                        if item_id_elem.text:
                            item_ids.append(item_id_elem.text)
            
            unique_item_ids = list(set(item_ids))  # 去重
            logger.info(f"从ZIP文件中提取到 {len(unique_item_ids)} 个唯一ItemID")
            return unique_item_ids
            
        except Exception as e:
            logger.error(f"从ZIP文件提取ItemID时出错: {e}")
            return []
    
    def get_item_details_batch(self, item_ids: List[str], access_token: str, 
                              task_id: str = None, progress_callback=None) -> List[Dict]:
        """批量获取商品详情"""
        results = []
        failed_items = []
        
        logger.info(f"开始批量处理 {len(item_ids)} 个ItemID，并发数: {self.max_workers}")
        
        def fetch_single_item(item_id: str) -> Optional[Dict]:
            """获取单个商品详情"""
            try:
                time.sleep(0.1)  # 避免API限制
                xml_response = self._get_item_details_with_curl(item_id, access_token)
                if xml_response:
                    parsed_result = self._parse_get_item_response(xml_response)
                    if parsed_result:
                        return parsed_result
                return None
            except Exception as e:
                logger.error(f"ItemID {item_id} 获取失败: {e}")
                return None
        
        # 并行处理
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item_id = {
                executor.submit(fetch_single_item, item_id): item_id 
                for item_id in item_ids
            }
            
            completed_count = 0
            total_count = len(item_ids)
            
            for future in as_completed(future_to_item_id, timeout=self.timeout):
                item_id = future_to_item_id[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    if result:
                        # 只处理USD货币的商品
                        if result.get('Currency') == 'USD':
                            results.append(result)
                            logger.debug(f"ItemID {item_id} (USD) 处理完成 ({completed_count}/{total_count})")
                        else:
                            logger.debug(f"ItemID {item_id} 跳过 (货币: {result.get('Currency', 'N/A')})")
                    else:
                        failed_items.append(item_id)
                except Exception as e:
                    logger.error(f"ItemID {item_id} 处理错误: {e}")
                    failed_items.append(item_id)
                
                # 进度回调
                if progress_callback:
                    progress_callback(completed_count, total_count)
        
        elapsed_time = time.time() - start_time
        logger.info(f"批量处理完成 - 成功: {len(results)}, 失败: {len(failed_items)}, 耗时: {elapsed_time:.2f}秒")
        return results
    
    def _get_item_details_with_curl(self, item_id: str, auth_token: str) -> Optional[str]:
        """使用curl获取商品详情（避免SSL问题）"""
        xml_request = f'''<?xml version="1.0" encoding="utf-8"?>
        <GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
            <ItemID>{item_id}</ItemID>
            <IncludeItemSpecifics>true</IncludeItemSpecifics>
            <DetailLevel>ItemReturnAttributes</DetailLevel>
        </GetItemRequest>'''
        
        try:
            cmd = [
                'curl', '-s', '-k',
                '--max-time', '30',
                '-X', 'POST',
                '-H', 'X-EBAY-API-COMPATIBILITY-LEVEL: 1217',
                '-H', f'X-EBAY-API-DEV-NAME: {self.config["EBAY_APP_ID"]}',
                '-H', f'X-EBAY-API-CERT-NAME: {self.config["EBAY_CERT_ID"]}',
                '-H', 'X-EBAY-API-CALL-NAME: GetItem',
                '-H', f'X-EBAY-API-IAF-TOKEN: {auth_token}',
                '-H', 'X-EBAY-API-SITEID: 0',
                '-H', 'Content-Type: text/xml',
                '--data-raw', xml_request,
                self.config['EBAY_TRADING_API_URL']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"curl failed for ItemID {item_id}, return code: {result.returncode}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Trading API timeout for ItemID {item_id}")
            return None
        except Exception as e:
            logger.error(f"Trading API call failed for ItemID {item_id}: {e}")
            return None
    
    def _parse_get_item_response(self, xml_response: str) -> Optional[Dict]:
        """解析GetItem响应XML"""
        try:
            parser = ET.XMLParser(encoding='utf-8')
            root = ET.fromstring(xml_response, parser=parser)
            
            ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
            
            item_data = {}
            
            # 基本信息提取
            elements_to_extract = {
                'ItemID': './/ebay:ItemID',
                'Title': './/ebay:Title',
                'SKU': './/ebay:SKU',
                'Quantity': './/ebay:Quantity'
            }
            
            for key, xpath in elements_to_extract.items():
                elem = root.find(xpath, ns)
                item_data[key] = elem.text if elem is not None else ''
            
            # 价格信息
            current_price = root.find('.//ebay:CurrentPrice', ns)
            if current_price is not None:
                item_data['CurrentPrice'] = current_price.text
                item_data['Currency'] = current_price.get('currencyID', '')
            else:
                item_data['CurrentPrice'] = ''
                item_data['Currency'] = ''
            
            # 类别信息
            primary_category = root.find('.//ebay:PrimaryCategory', ns)
            if primary_category is not None:
                category_id = primary_category.find('ebay:CategoryID', ns)
                category_name = primary_category.find('ebay:CategoryName', ns)
                item_data['CategoryID'] = category_id.text if category_id is not None else ''
                item_data['CategoryName'] = category_name.text if category_name is not None else ''
            
            # Item Specifics
            specifics_dict = {}
            for specific in root.findall('.//ebay:ItemSpecifics/ebay:NameValueList', ns):
                name_elem = specific.find('ebay:Name', ns)
                value_elem = specific.find('ebay:Value', ns)
                if name_elem is not None and value_elem is not None:
                    specifics_dict[name_elem.text] = value_elem.text
            
            item_data['ItemSpecifics'] = specifics_dict
            
            return item_data
            
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {e}")
            return None
        except Exception as e:
            logger.error(f"GetItem响应解析错误: {e}")
            return None
