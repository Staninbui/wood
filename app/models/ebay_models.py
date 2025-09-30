"""
eBay相关数据模型
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class EbayToken:
    """eBay访问令牌模型"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = 'Bearer'
    expires_in: Optional[int] = None
    debug_mode: bool = False


@dataclass
class InventoryTask:
    """库存任务模型"""
    task_id: str
    status: str
    creation_date: Optional[str] = None
    completion_date: Optional[str] = None
    feed_type: str = 'LMS_ACTIVE_INVENTORY_REPORT'
    schema_version: str = '1.0'
    location: Optional[str] = None


@dataclass
class ItemDetails:
    """商品详情模型"""
    item_id: str
    title: str
    sku: str
    current_price: str
    currency: str
    quantity: str
    category_id: str
    category_name: str
    item_specifics: Dict[str, str]
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'ItemID': self.item_id,
            'Title': self.title,
            'SKU': self.sku,
            'CurrentPrice': self.current_price,
            'Currency': self.currency,
            'Quantity': self.quantity,
            'CategoryID': self.category_id,
            'CategoryName': self.category_name,
            'ItemSpecifics': self.item_specifics
        }


@dataclass
class EbayTemplateRow:
    """eBay模板行数据模型"""
    action: str = 'Revise'
    category_name: str = ''
    item_number: str = ''
    title: str = ''
    listing_site: str = 'US'
    currency: str = 'USD'
    start_price: str = ''
    buy_it_now_price: str = ''
    available_quantity: str = ''
    relationship: str = ''
    relationship_details: str = ''
    custom_label_sku: str = ''
    item_specifics: Dict[str, str] = None
    
    def __post_init__(self):
        if self.item_specifics is None:
            self.item_specifics = {}
    
    def to_dict(self) -> Dict:
        """转换为字典格式，包含C:前缀的Item Specifics"""
        base_dict = {
            'Action': self.action,
            'Category name': self.category_name,
            'Item number': self.item_number,
            'Title': self.title,
            'Listing site': self.listing_site,
            'Currency': self.currency,
            'Start price': self.start_price,
            'Buy It Now price': self.buy_it_now_price,
            'Available quantity': self.available_quantity,
            'Relationship': self.relationship,
            'Relationship details': self.relationship_details,
            'Custom label (SKU)': self.custom_label_sku
        }
        
        # 添加Item Specifics为C:格式
        for spec_name, spec_value in self.item_specifics.items():
            base_dict[f"C:{spec_name}"] = spec_value
        
        return base_dict
