import os
import multiprocessing

# 服务器套接字
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# 工作进程 - Cloud Run优化设置
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = 'gevent'
worker_connections = 500
max_requests = 1000
max_requests_jitter = 50

# 超时设置 - Cloud Run调整
timeout = 120
keepalive = 2
graceful_timeout = 30

# 日志设置
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名
proc_name = 'wood-ebay-app'

# 安全设置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 预加载应用
preload_app = True

def when_ready(server):
    server.log.info("サーバー準備完了")

def worker_int(worker):
    worker.log.info("ワーカー中断: %s", worker.pid)

def pre_fork(server, worker):
    server.log.info("ワーカーフォーク前: %s", worker.pid)

def post_fork(server, worker):
    server.log.info("ワーカーフォーク後: %s", worker.pid)
