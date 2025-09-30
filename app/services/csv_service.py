"""
CSV生成服务层
"""
import os
import pandas as pd
import tempfile
import logging
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class CSVService:
    """CSV生成服务类"""
    
    def __init__(self, config=None):
        if config:
            self.temp_folder = config.get('TEMP_FOLDER', tempfile.gettempdir())
        else:
            self.temp_folder = current_app.config.get('TEMP_FOLDER', tempfile.gettempdir())
    
    def generate_enhanced_csv(self, item_data_list: List[Dict], task_id: str) -> Optional[str]:
        """生成增强CSV文件"""
        try:
            if not item_data_list:
                logger.error("没有数据可生成CSV")
                return None
            
            # 转换数据为eBay File Exchange格式
            ebay_template_data = self._convert_to_ebay_template(item_data_list)
            
            # 生成CSV内容
            csv_content = self._create_csv_content(ebay_template_data)
            
            # 确保临时目录存在
            os.makedirs(self.temp_folder, exist_ok=True)
            
            # 保存到临时文件
            temp_file_path = os.path.join(self.temp_folder, f'enhanced_csv_{task_id}.csv')
            with open(temp_file_path, 'wb') as f:
                f.write(csv_content)
            
            logger.info(f"增强CSV生成完成: {temp_file_path}, 包含 {len(item_data_list)} 条记录")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"生成增强CSV时出错: {e}")
            return None
    
    def generate_basic_csv(self, listings_data: List[Dict]) -> BytesIO:
        """生成基础CSV文件"""
        try:
            df = pd.DataFrame(listings_data)
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return output
        except Exception as e:
            logger.error(f"生成基础CSV时出错: {e}")
            raise
    
    def generate_excel(self, listings_data: List[Dict]) -> BytesIO:
        """生成Excel文件"""
        try:
            df = pd.DataFrame(listings_data)
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='eBay Listings', index=False)
                
                # 设置列宽
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
            return output
            
        except Exception as e:
            logger.error(f"生成Excel时出错: {e}")
            raise
    
    def _convert_to_ebay_template(self, item_data_list: List[Dict]) -> List[Dict]:
        """转换数据为eBay模板格式"""
        ebay_template_data = []
        
        for item in item_data_list:
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
            
            # 添加Item Specifics为C:格式列
            item_specifics = item.get('ItemSpecifics', {})
            for spec_name, spec_value in item_specifics.items():
                column_name = f"C:{spec_name}"
                row[column_name] = spec_value
            
            ebay_template_data.append(row)
        
        return ebay_template_data
    
    def _create_csv_content(self, data: List[Dict]) -> bytes:
        """创建CSV内容"""
        output = BytesIO()
        
        # 写入INFO头部
        info_header = "#INFO,Version=1.0.0,Template= eBay-active-revise-price-quantity-download_US\n"
        output.write(info_header.encode('utf-8-sig'))
        
        # 写入数据
        df = pd.DataFrame(data)
        csv_content = df.to_csv(index=False, encoding='utf-8')
        output.write(csv_content.encode('utf-8'))
        
        return output.getvalue()
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"临时文件已清理: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def get_temp_file_path(self, task_id: str) -> str:
        """获取临时文件路径"""
        return os.path.join(self.temp_folder, f'enhanced_csv_{task_id}.csv')
    
    def generate_filename(self, task_id: str, file_type: str = 'csv') -> str:
        """生成文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if file_type == 'csv':
            return f"ebay_revise_template_{task_id}_{timestamp}.csv"
        elif file_type == 'xlsx':
            return f"ebay_listings_{timestamp}.xlsx"
        else:
            return f"ebay_listings_{timestamp}.{file_type}"
