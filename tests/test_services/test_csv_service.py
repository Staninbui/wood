"""
CSV服务测试
"""
import pytest
import tempfile
import os
from app.services.csv_service import CSVService


@pytest.fixture
def csv_service(app):
    """创建CSV服务实例"""
    with app.app_context():
        return CSVService()


@pytest.fixture
def sample_item_data():
    """示例商品数据"""
    return [
        {
            'ItemID': '123456789',
            'Title': 'Test Item 1',
            'SKU': 'TEST-001',
            'CurrentPrice': '99.99',
            'Currency': 'USD',
            'Quantity': '10',
            'CategoryID': '12345',
            'CategoryName': 'Electronics',
            'ItemSpecifics': {
                'Brand': 'TestBrand',
                'Color': 'Black',
                'Size': 'Large'
            }
        },
        {
            'ItemID': '987654321',
            'Title': 'Test Item 2',
            'SKU': 'TEST-002',
            'CurrentPrice': '49.99',
            'Currency': 'USD',
            'Quantity': '5',
            'CategoryID': '67890',
            'CategoryName': 'Fashion',
            'ItemSpecifics': {
                'Brand': 'TestBrand2',
                'Material': 'Cotton',
                'Style': 'Casual'
            }
        }
    ]


def test_generate_enhanced_csv(csv_service, sample_item_data):
    """测试生成增强CSV"""
    task_id = 'test-task-123'
    
    # 生成CSV文件
    file_path = csv_service.generate_enhanced_csv(sample_item_data, task_id)
    
    assert file_path is not None
    assert os.path.exists(file_path)
    
    # 检查文件内容
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        
    # 检查INFO头部
    assert '#INFO,Version=1.0.0' in content
    
    # 检查基本列
    assert 'Action' in content
    assert 'Item number' in content
    assert 'Title' in content
    
    # 检查Item Specifics列（C:前缀）
    assert 'C:Brand' in content
    assert 'C:Color' in content
    assert 'C:Material' in content
    
    # 检查数据行
    assert 'Test Item 1' in content
    assert 'Test Item 2' in content
    assert 'TestBrand' in content
    
    # 清理测试文件
    csv_service.cleanup_temp_file(file_path)


def test_generate_basic_csv(csv_service):
    """测试生成基础CSV"""
    listings_data = [
        {
            'sku': 'TEST-001',
            'title': 'Test Item',
            'price': 99.99,
            'quantity': 10
        }
    ]
    
    output = csv_service.generate_basic_csv(listings_data)
    
    assert output is not None
    
    # 检查内容
    content = output.getvalue().decode('utf-8-sig')
    assert 'sku' in content
    assert 'title' in content
    assert 'TEST-001' in content
    assert 'Test Item' in content


def test_generate_filename(csv_service):
    """测试文件名生成"""
    task_id = 'test-task-123'
    
    # 测试CSV文件名
    csv_filename = csv_service.generate_filename(task_id, 'csv')
    assert csv_filename.startswith('ebay_revise_template_test-task-123_')
    assert csv_filename.endswith('.csv')
    
    # 测试Excel文件名
    xlsx_filename = csv_service.generate_filename(task_id, 'xlsx')
    assert xlsx_filename.startswith('ebay_listings_')
    assert xlsx_filename.endswith('.xlsx')


def test_get_temp_file_path(csv_service):
    """测试临时文件路径生成"""
    task_id = 'test-task-123'
    file_path = csv_service.get_temp_file_path(task_id)
    
    assert 'enhanced_csv_test-task-123.csv' in file_path
