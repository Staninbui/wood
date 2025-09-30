"""
pytest配置文件
"""
import pytest
import os
import tempfile
from app import create_app


@pytest.fixture
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 测试配置
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'EBAY_APP_ID': 'test-app-id',
        'EBAY_CERT_ID': 'test-cert-id',
        'EBAY_RU_NAME': 'http://localhost:8080/auth/callback',
        'WTF_CSRF_ENABLED': False
    }
    
    app = create_app('testing')
    app.config.update(test_config)
    
    with app.app_context():
        yield app
    
    # 清理临时文件
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def auth_session(client):
    """创建已认证的会话"""
    with client.session_transaction() as sess:
        sess['ebay_token'] = {
            'access_token': 'test-access-token',
            'token_type': 'Bearer',
            'debug_mode': True
        }
    return client
