import os
import multiprocessing

# サーバーソケット
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# ワーカープロセス
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'gevent'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# タイムアウト設定
timeout = 300  # CPU集約的タスクを考慮
keepalive = 2
graceful_timeout = 30

# ログ設定
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス名
proc_name = 'wood-ebay-app'

# セキュリティ
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# プリロード
preload_app = True

# メモリ管理
max_requests = 1000
max_requests_jitter = 50

def when_ready(server):
    server.log.info("サーバー準備完了")

def worker_int(worker):
    worker.log.info("ワーカー中断: %s", worker.pid)

def pre_fork(server, worker):
    server.log.info("ワーカーフォーク前: %s", worker.pid)

def post_fork(server, worker):
    server.log.info("ワーカーフォーク後: %s", worker.pid)
