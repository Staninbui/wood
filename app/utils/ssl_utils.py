"""
SSL工具类
"""
import ssl
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import ssl_


# 完全禁用SSL验证以防止递归错误
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def patched_create_urllib3_context(ssl_version=None, cert_reqs=None, options=None, ciphers=None):
    """修补的urllib3上下文创建函数"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


# 应用补丁
ssl_.create_urllib3_context = patched_create_urllib3_context


class NoSSLAdapter(HTTPAdapter):
    """绕过SSL验证的HTTP适配器"""
    
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl.create_default_context()
        kwargs['ssl_context'].check_hostname = False
        kwargs['ssl_context'].verify_mode = ssl.CERT_NONE
        return super().init_poolmanager(*args, **kwargs)


def create_ssl_session():
    """创建配置了SSL绕过的requests会话"""
    session = requests.Session()
    session.verify = False
    session.mount('https://', NoSSLAdapter())
    return session
