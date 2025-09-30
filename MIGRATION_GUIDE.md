# Wood项目迁移指南 - v1.0 到 v2.0

本指南将帮助您从旧版本的Wood项目迁移到新的企业级架构版本。

## 🔄 主要变更概览

### 架构变更
- **单文件应用** → **模块化架构**
- **直接配置** → **多环境配置管理**
- **内联错误处理** → **统一错误处理系统**
- **混合代码** → **清晰的层次分离**

### 文件结构变更

#### 旧结构 (v1.0)
```
wood/
├── app.py                    # 所有功能集中在一个文件
├── config.py                 # 简单配置
├── xml_processor.py          # XML处理
├── progress_manager.py       # 进度管理
├── static/
├── templates/
└── requirements.txt
```

#### 新结构 (v2.0)
```
wood/
├── app/                      # 应用包
│   ├── __init__.py          # 应用工厂
│   ├── api/                 # API路由层
│   ├── services/            # 业务逻辑层
│   ├── utils/               # 工具层
│   ├── models/              # 数据模型
│   ├── static/
│   └── templates/
├── config/                   # 配置管理
├── requirements/             # 分层依赖管理
├── tests/                    # 测试文件
├── run.py                    # 开发入口
└── wsgi.py                   # 生产入口
```

## 📋 迁移步骤

### 1. 备份现有项目
```bash
cp -r wood wood_v1_backup
```

### 2. 更新依赖文件
将原来的 `requirements.txt` 内容移动到 `requirements/base.txt`：

```bash
mkdir requirements
mv requirements.txt requirements/base.txt
```

### 3. 环境变量迁移
原来的环境变量配置保持不变，但现在支持更多配置选项：

```bash
# 新增的可选配置
MAX_WORKERS=4
TASK_TIMEOUT=300
LOG_LEVEL=INFO
```

### 4. 启动方式变更

#### 开发环境
```bash
# 旧方式
python app.py

# 新方式
python run.py
```

#### 生产环境
```bash
# 旧方式
gunicorn app:app

# 新方式
gunicorn -c gunicorn.conf.py wsgi:application
```

### 5. API端点变更

大部分API端点保持兼容，但有一些组织上的变更：

#### 认证相关
- `GET /login` → `GET /auth/login`
- `GET /callback` → `GET /auth/callback`
- `GET /logout` → `GET /auth/logout`

#### 报告相关
- `POST /generate-report` → `POST /api/reports/generate`
- `GET /check-feed-status` → `GET /api/reports/status`
- `GET /export-csv` → `GET /api/reports/export/csv`
- `GET /export-excel` → `GET /api/reports/export/excel`

#### 任务相关
- `POST /query-task-by-id` → `POST /api/tasks/query`
- `GET /download-task-result/<task_id>` → `GET /api/tasks/download/<task_id>`
- `GET /generate-enhanced-csv/<task_id>` → `GET /api/tasks/enhanced-csv/<task_id>`

### 6. 代码迁移（如有自定义修改）

如果您对原代码进行了自定义修改，需要将这些修改迁移到新的模块结构中：

#### eBay API相关修改
- 原来在 `app.py` 中的eBay API调用 → `app/services/ebay_service.py`

#### XML处理相关修改
- 原来的 `xml_processor.py` → `app/services/xml_service.py`

#### CSV生成相关修改
- 原来在 `app.py` 中的CSV生成逻辑 → `app/services/csv_service.py`

#### 进度管理相关修改
- 原来的 `progress_manager.py` → `app/utils/progress_manager.py`

## 🔧 配置迁移

### 环境配置
新版本支持多环境配置，您可以根据需要创建不同的配置：

```python
# config/development.py - 开发环境
DEBUG = True
LOG_LEVEL = 'DEBUG'

# config/production.py - 生产环境  
DEBUG = False
LOG_LEVEL = 'INFO'

# config/testing.py - 测试环境
TESTING = True
```

### 日志配置
新版本提供了更完善的日志配置：

```python
# 开发环境：控制台输出
# 生产环境：文件日志 + 轮转
# 可通过 LOG_LEVEL 环境变量控制日志级别
```

## 🧪 测试迁移

新版本包含了完整的测试框架：

```bash
# 安装测试依赖
pip install -r requirements/development.txt

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=app tests/
```

## 🚀 部署迁移

### Docker部署
Dockerfile已更新为多阶段构建，提供更好的性能和安全性：

```bash
# 构建镜像
docker build -t wood-ebay-app:v2 .

# 运行容器
docker run -p 8080:8080 wood-ebay-app:v2
```

### Cloud Run部署
部署配置保持兼容，但现在使用新的入口点：

```yaml
# cloudbuild.yaml 中的更新
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/wood-ebay-app:v2', '.']
```

## ⚠️ 注意事项

### 1. 数据兼容性
- 会话数据格式保持兼容
- 临时文件路径可能有变化
- 日志文件位置可能有变化

### 2. 性能影响
- 新架构可能有轻微的启动时间增加
- 内存使用可能略有优化
- 并发处理性能应该有所提升

### 3. 功能变更
- 错误处理更加统一和详细
- 日志记录更加结构化
- API响应格式保持兼容

## 🔍 验证迁移

迁移完成后，请验证以下功能：

### 1. 基础功能
- [ ] 应用启动正常
- [ ] 健康检查端点工作
- [ ] 静态文件加载正常

### 2. 认证功能
- [ ] eBay OAuth登录流程
- [ ] 会话管理
- [ ] 登出功能

### 3. 核心功能
- [ ] 报告生成
- [ ] 任务状态查询
- [ ] CSV导出
- [ ] 进度显示

### 4. 错误处理
- [ ] API错误响应
- [ ] 日志记录
- [ ] 异常处理

## 🆘 故障排除

### 常见问题

#### 1. 导入错误
```
ModuleNotFoundError: No module named 'app'
```
**解决方案**: 确保在项目根目录运行，并且已安装所有依赖。

#### 2. 配置错误
```
KeyError: 'EBAY_APP_ID'
```
**解决方案**: 检查环境变量配置，确保所有必需的eBay API配置都已设置。

#### 3. 端口冲突
```
Address already in use
```
**解决方案**: 检查端口8080是否被占用，或通过PORT环境变量指定其他端口。

### 回滚方案
如果迁移遇到问题，可以快速回滚到v1.0版本：

```bash
# 停止新版本
pkill -f "python run.py"

# 切换到备份版本
cd wood_v1_backup

# 启动旧版本
python app.py
```

## 📞 获取帮助

如果在迁移过程中遇到问题：

1. 检查本迁移指南的故障排除部分
2. 查看新版本的README_v2.md文档
3. 检查日志文件中的错误信息
4. 提交GitHub Issue并提供详细的错误信息

---

迁移完成后，您将享受到更好的代码组织、更强的可维护性和更完善的错误处理！
