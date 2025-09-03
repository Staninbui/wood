# 使用官方的轻量级Python镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止Python写入.pyc文件
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件到工作目录
COPY . .

# 使用Gunicorn作为生产环境的WSGI服务器
# Cloud Run会自动注入PORT环境变量
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
