"""
应用基础测试
"""
import pytest
from app import create_app


def test_create_app():
    """测试应用工厂函数"""
    app = create_app('testing')
    assert app.config['TESTING'] is True


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['service'] == 'wood-ebay-app'


def test_index_page(client):
    """测试首页"""
    response = client.get('/')
    assert response.status_code == 200


def test_auth_required_endpoints(client):
    """测试需要认证的端点"""
    # 测试未认证访问
    response = client.post('/api/reports/generate')
    assert response.status_code == 401
    
    response = client.get('/api/reports/status')
    assert response.status_code == 401


def test_auth_required_with_session(auth_session):
    """测试已认证的访问"""
    # 这里可以测试需要认证的端点
    response = auth_session.get('/api/reports/recent')
    # 由于没有真实的eBay API，这里可能会返回错误，但不应该是401
    assert response.status_code != 401
