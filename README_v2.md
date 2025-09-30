# Wood - 企业级eBay商品管理系统 v2.0

> 专业的eBay商品属性管理和CSV导出工具，采用企业级Flask架构重构

## 🚀 新版本特性

### 架构升级
- **企业级项目结构** - 采用标准的Flask应用工厂模式
- **模块化设计** - 清晰的服务层、API层、工具层分离
- **配置管理** - 多环境配置支持（开发/生产/测试）
- **错误处理** - 统一的错误处理和日志系统
- **代码质量** - 类型提示、文档字符串、装饰器模式

### 核心功能
1. **eBay OAuth 2.0认证** - 安全登录eBay账户
2. **在庫レポート生成** - 使用eBay Feed API获取Active Inventory Report
3. **XML文件处理** - 解析ZIP格式的eBay报告文件，提取ItemID
4. **商品详情获取** - 使用eBay Trading API批量获取商品详细信息和Item Specifics
5. **CSV导出** - 生成eBay File Exchange格式的CSV文件，包含Item Specifics
6. **实时进度显示** - 使用SSE和轮询方式显示处理进度

## 📁 新项目结构

```
wood/
├── app/                          # 应用核心包
│   ├── __init__.py              # Flask应用工厂
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   └── ebay_models.py       # eBay相关数据模型
│   ├── api/                     # API路由
│   │   ├── __init__.py
│   │   ├── main.py              # 主页面路由
│   │   ├── auth.py              # 认证相关路由
│   │   ├── reports.py           # 报告生成路由
│   │   └── tasks.py             # 任务管理路由
│   ├── services/                # 业务逻辑服务层
│   │   ├── __init__.py
│   │   ├── ebay_service.py      # eBay API服务
│   │   ├── xml_service.py       # XML处理服务
│   │   └── csv_service.py       # CSV生成服务
│   ├── utils/                   # 工具类
│   │   ├── __init__.py
│   │   ├── ssl_utils.py         # SSL处理工具
│   │   ├── progress_manager.py  # 进度管理器
│   │   ├── decorators.py        # 装饰器
│   │   └── error_handlers.py    # 错误处理器
│   ├── static/                  # 静态文件
│   └── templates/               # 模板文件
├── config/                      # 配置文件
│   ├── __init__.py
│   ├── base.py                  # 基础配置
│   ├── development.py           # 开发环境配置
│   ├── production.py            # 生产环境配置
│   └── testing.py               # 测试环境配置
├── requirements/                # 依赖管理
│   ├── base.txt                 # 基础依赖
│   ├── development.txt          # 开发依赖
│   └── production.txt           # 生产依赖
├── tests/                       # 测试文件
├── logs/                        # 日志文件
├── run.py                       # 开发环境入口
├── wsgi.py                      # 生产环境入口
└── gunicorn.conf.py             # Gunicorn配置
```

## 🔧 开发环境设置

### 前提条件
- Python 3.9以上
- eBay Developer Account
- eBay App ID, Cert ID, RuName

### 1. 克隆项目
```bash
git clone <repository-url>
cd wood
```

### 2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
# 开发环境
pip install -r requirements/development.txt

# 生产环境
pip install -r requirements/production.txt
```

### 4. 环境变量配置
创建 `.env` 文件：
```bash
# eBay API设置
EBAY_APP_ID=your_ebay_app_id_here
EBAY_CERT_ID=your_ebay_cert_id_here
EBAY_RU_NAME=your_redirect_uri_here

# 本地调试用 - 设置此项可跳过OAuth流程
EBAY_USER_ACCESS_TOKEN=your_user_access_token_here

# Flask设置
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
LOG_LEVEL=DEBUG

# 性能设置
MAX_WORKERS=4
TASK_TIMEOUT=300
```

### 5. 启动开发服务器
```bash
python run.py
```

应用将在 `http://localhost:8080` 启动

## 🌐 生产环境部署

### 使用Gunicorn
```bash
gunicorn -c gunicorn.conf.py wsgi:application
```

### 使用Docker
```bash
docker build -t wood-ebay-app .
docker run -p 8080:8080 wood-ebay-app
```

### Google Cloud Run部署
```bash
gcloud builds submit --config cloudbuild.yaml .
```

## 🏗️ 架构设计

### 应用工厂模式
- 使用 `create_app()` 函数创建Flask应用实例
- 支持多环境配置
- 蓝图注册和错误处理器注册

### 服务层架构
- **EbayService**: eBay API调用封装
- **XMLService**: XML文件处理和ItemID提取
- **CSVService**: CSV文件生成和格式化

### 装饰器模式
- `@login_required`: 登录验证
- `@handle_api_errors`: API错误处理
- `@validate_task_id`: 任务ID验证

### 进度管理
- 线程安全的进度跟踪
- 支持SSE和轮询两种进度推送方式
- 详细的任务状态管理

## 📋 API端点

### 认证相关
- `GET /auth/login` - eBay OAuth登录
- `GET /auth/callback` - OAuth回调处理
- `GET /auth/logout` - 登出
- `GET /auth/status` - 认证状态检查

### 报告管理
- `POST /api/reports/generate` - 生成新报告
- `GET /api/reports/status` - 检查报告状态
- `GET /api/reports/recent` - 获取最近报告
- `GET /api/reports/export/csv` - 导出CSV
- `GET /api/reports/export/excel` - 导出Excel

### 任务管理
- `POST /api/tasks/query` - 查询任务状态
- `GET /api/tasks/download/<task_id>` - 下载任务结果
- `GET|HEAD /api/tasks/enhanced-csv/<task_id>` - 生成增强CSV
- `GET /api/tasks/progress/<task_id>` - SSE进度推送
- `GET /api/tasks/progress-poll/<task_id>` - 轮询进度

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_services/

# 生成覆盖率报告
pytest --cov=app tests/
```

## 📊 监控和日志

### 日志配置
- 开发环境：控制台输出
- 生产环境：文件日志 + 轮转
- 结构化日志格式

### 健康检查
- `GET /health` - 应用健康状态

## 🔒 安全特性

- HTTPS强制（生产环境）
- 安全的会话配置
- CSRF保护
- 输入验证和清理
- SSL证书验证绕过（解决eBay API问题）

## 🚀 性能优化

- 并发处理（ThreadPoolExecutor）
- 连接池管理
- 内存优化的大文件处理
- Gunicorn + Gevent异步处理
- 静态文件缓存

## 📈 扩展性

- 模块化架构便于功能扩展
- 服务层抽象便于API替换
- 配置驱动的环境管理
- 插件式错误处理

## 🤝 开发指南

### 代码规范
- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 使用MyPy进行类型检查
- 遵循PEP 8编码规范

### 提交规范
- feat: 新功能
- fix: 错误修复
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关

## 📞 支持

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- 邮件支持

---

## 版本历史

### v2.0.0 (2024-01-XX)
- 🏗️ 企业级架构重构
- 📦 模块化设计
- 🔧 多环境配置支持
- 🛡️ 增强的错误处理
- 📊 改进的日志系统

### v1.0.0
- 基础功能实现
- eBay API集成
- CSV导出功能
