# Wood eBay管理系统 - 项目结构说明

## 📁 项目目录结构

```
wood/
├── app/                          # 应用主目录
│   ├── __init__.py              # 应用工厂函数
│   ├── api/                     # API路由模块
│   │   ├── auth.py             # 认证相关路由
│   │   ├── main.py             # 主页面路由
│   │   ├── reports.py          # 报告生成路由
│   │   └── tasks.py            # 任务处理路由
│   ├── services/                # 业务逻辑服务
│   │   ├── csv_service.py      # CSV生成服务
│   │   ├── ebay_service.py     # eBay API服务
│   │   └── xml_service.py      # XML解析服务
│   ├── utils/                   # 工具函数
│   │   ├── decorators.py       # 装饰器
│   │   ├── error_handlers.py   # 错误处理
│   │   ├── progress_manager.py # 进度管理
│   │   └── ssl_utils.py        # SSL工具
│   ├── static/                  # 静态文件
│   │   └── app.js              # 前端JavaScript
│   └── templates/               # HTML模板
│       ├── index.html          # 首页
│       └── dashboard.html      # 仪表板
│
├── config/                      # 配置模块
│   ├── __init__.py             # 配置入口
│   ├── base.py                 # 基础配置
│   ├── development.py          # 开发环境配置
│   ├── production.py           # 生产环境配置
│   └── testing.py              # 测试环境配置
│
├── tests/                       # 测试目录
│   ├── test_api/               # API测试
│   ├── test_services/          # 服务测试
│   └── test_utils/             # 工具测试
│
├── requirements/                # 依赖管理
│   ├── base.txt                # 基础依赖
│   ├── dev.txt                 # 开发依赖
│   └── prod.txt                # 生产依赖
│
├── logs/                        # 日志目录
├── temp/                        # 临时文件目录
├── uploads/                     # 上传文件目录
│
├── config.py                    # 配置入口文件
├── run.py                       # 开发服务器入口
├── wsgi.py                      # 生产环境WSGI入口
├── gunicorn.conf.py            # Gunicorn配置
├── Dockerfile                   # Docker配置
├── cloudbuild.yaml             # Cloud Build配置
├── requirements.txt            # 依赖清单
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略文件
├── README.md                   # 项目说明
├── MIGRATION_GUIDE.md          # 迁移指南
└── PROJECT_STRUCTURE.md        # 本文件
```

## 🚀 启动方式

### 开发环境
```bash
# 使用run.py启动开发服务器
python run.py
```

### 生产环境
```bash
# 使用Gunicorn启动
gunicorn -c gunicorn.conf.py wsgi:application
```

### Docker部署
```bash
# 构建镜像
docker build -t wood-ebay-app .

# 运行容器
docker run -p 8080:8080 --env-file .env wood-ebay-app
```

## 📝 核心文件说明

### 根目录文件

- **`config.py`**: 配置管理入口，导出不同环境的配置
- **`run.py`**: 开发服务器启动脚本
- **`wsgi.py`**: WSGI应用入口，用于生产环境部署
- **`gunicorn.conf.py`**: Gunicorn服务器配置

### 应用模块

- **`app/__init__.py`**: 应用工厂函数，创建和配置Flask应用
- **`app/api/`**: RESTful API路由定义
- **`app/services/`**: 业务逻辑和外部服务集成
- **`app/utils/`**: 通用工具函数和辅助类

## 🔄 版本历史

### v2.0.0 (当前版本)
- ✅ 重构为模块化架构
- ✅ 分离业务逻辑和路由
- ✅ 改进错误处理和日志记录
- ✅ 添加进度跟踪功能
- ✅ 优化CSV生成流程

### v1.0.0 (已废弃)
- ❌ 单体应用文件 (`app.py`)
- ❌ 混合的业务逻辑和路由
- ❌ 有限的错误处理

## 📚 相关文档

- [README.md](README.md) - 项目概述和快速开始
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 从v1迁移到v2的指南
- [deploy.md](deploy.md) - 部署说明
- [prd.md](prd.md) - 产品需求文档

## 🛠️ 开发指南

### 添加新功能

1. **创建服务类** (如果需要)
   ```python
   # app/services/new_service.py
   class NewService:
       def __init__(self, config=None):
           self.config = config or current_app.config
   ```

2. **创建API路由**
   ```python
   # app/api/new_routes.py
   from flask import Blueprint
   
   new_bp = Blueprint('new', __name__)
   
   @new_bp.route('/endpoint')
   def endpoint():
       pass
   ```

3. **注册蓝图**
   ```python
   # app/__init__.py
   from app.api.new_routes import new_bp
   app.register_blueprint(new_bp, url_prefix='/api/new')
   ```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_services/test_ebay_service.py

# 查看覆盖率
pytest --cov=app tests/
```

## 🔒 安全注意事项

1. **环境变量**: 所有敏感信息通过环境变量配置
2. **SSL/TLS**: 生产环境强制使用HTTPS
3. **Session安全**: 启用HttpOnly和Secure cookie
4. **API密钥**: 不要在代码中硬编码API密钥

## 📞 支持

如有问题，请查看：
- [GitHub Issues](https://github.com/yourusername/wood/issues)
- [文档](README.md)
- [迁移指南](MIGRATION_GUIDE.md)
