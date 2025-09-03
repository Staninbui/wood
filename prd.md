# **eBay商品特性导出工具 \- 开发计划**

## **1\. 项目概述 (Project Overview)**

**目标:** 创建一个部署在Google Cloud Run上的Web应用。该应用允许eBay卖家通过OAuth安全授权，然后触发一个后端任务，该任务会通过eBay Feed API获取卖家所有“在线刊登(Active Listings)”的商品特性(Item Specifics)，并生成一个符合eBay File Exchange修订格式的CSV文件，供卖家下载和本地编辑。

**技术栈 (Tech Stack):**

* **后端框架:** **Flask** \- 轻量级、灵活，非常适合快速原型开发和构建API服务。  
* **eBay API交互:** ebay-sdk-python \- 官方SDK，简化了OAuth认证和API调用的复杂性。  
* **数据处理:** pandas \- 强大的数据分析库，用于解析从eBay获取的数据并高效地生成CSV。  
* **部署平台:** **Google Cloud Run** \- 全托管的无服务器平台，可自动扩缩容，按使用量付费。  
* **安全凭证管理:** **Google Secret Manager** \- 安全存储eBay API密钥等敏感信息，是云端部署的最佳实践。  
* **容器化:** **Docker** \- 用于打包应用及其所有依赖，确保在任何环境中都能一致地运行。

## **2\. 开发里程碑 (Development Milestones)**

我们将项目分解为五个核心阶段，以便于迭代开发、快速验证和风险控制。

### **里程碑一：环境搭建与基础框架 (M1: Environment & Foundation)**

**目标:** 搭建本地开发环境，配置云端基础设施，并成功部署一个最简单的 "Hello World" 应用到Cloud Run，以确保整个部署流程畅通无阻。

1. **eBay开发者账户配置:**  
   * 注册 [eBay开发者账户](https://developer.ebay.com/)。  
   * 创建一个新的应用，获取App ID (Client ID)和Cert ID (Client Secret)。  
   * 配置应用的OAuth Redirect URI。本地测试时可设为 http://127.0.0.1:8080/callback，后续部署后需更新为Cloud Run服务的URL。  
2. **Google Cloud项目配置:**  
   * 创建一个新的GCP项目。  
   * 在项目中启用以下API服务：Cloud Run API, Secret Manager API, Cloud Build API。  
   * 安装并配置 gcloud 命令行工具。  
3. **本地开发环境:**  
   * 安装 Python 3.9+。  
   * 创建并激活Python虚拟环境 (python \-m venv venv)。  
   * 初始化一个Git仓库进行版本控制。  
4. **Flask应用骨架:**  
   * 创建 app.py，包含一个返回 "Hello World" 的根路由 (/)。  
   * 创建 requirements.txt，添加 Flask 和 gunicorn。  
   * 创建 Dockerfile，用于将应用容器化。这是一个生产级的Dockerfile模板：  
     \# 使用官方的轻量级Python镜像  
     FROM python:3.9-slim

     \# 设置工作目录  
     WORKDIR /app

     \# 设置环境变量，防止Python写入.pyc文件  
     ENV PYTHONDONTWRITEBYTECODE 1  
     ENV PYTHONUNBUFFERED 1

     \# 复制依赖文件并安装  
     COPY requirements.txt .  
     RUN pip install \--no-cache-dir \-r requirements.txt

     \# 复制所有项目文件到工作目录  
     COPY . .

     \# 使用Gunicorn作为生产环境的WSGI服务器  
     \# Cloud Run会自动注入PORT环境变量  
     CMD exec gunicorn \--bind :$PORT \--workers 1 \--threads 8 \--timeout 0 app:app

5. **首次部署验证:**  
   * 使用 gcloud run deploy 命令将 "Hello World" 应用部署到Cloud Run。确保服务可以公开访问，并验证部署流程的正确性。

### **里程碑二：eBay OAuth 2.0 认证集成 (M2: eBay OAuth 2.0 Integration)**

**目标:** 实现完整的用户认证流程，让卖家能够安全地登录并授权我们的应用访问其eBay账户数据。

1. **安装SDK:**  
   * 在 requirements.txt 中添加 ebay-sdk-python。  
2. **安全存储凭证:**  
   * 在 **Google Secret Manager** 中创建Secrets，用于存储：  
     * EBAY\_APP\_ID  
     * EBAY\_CERT\_ID  
     * EBAY\_RU\_NAME (在eBay开发者后台配置的Redirect URI Name)  
   * 在Cloud Run服务配置中，将这些Secrets挂载为环境变量，以便应用在运行时安全地访问它们。**严禁将任何密钥硬编码在代码中。**  
3. **实现认证路由:**  
   * **/login (登录入口):**  
     * 从环境变量中读取eBay App ID等配置。  
     * 使用eBay SDK生成用户授权URL。  
     * 将用户重定向到此URL，用户将在eBay网站上完成登录和授权。  
   * **/callback (授权回调):**  
     * 用户在eBay授权后，会被重定向到此URL。  
     * 从URL的查询参数中获取授权码 (code)。  
     * 使用此授权码，通过SDK向eBay交换访问令牌（Access Token）和刷新令牌（Refresh Token）。  
     * **安全地存储令牌:** 对于原型，可以使用Flask的服务器端session来临时存储令牌。  
4. **更新主页逻辑:**  
   * 在主页 (/) 检查session中是否存在有效的访问令牌。  
   * 如果存在，显示 "已登录" 状态和 "生成报告" 的按钮。  
   * 如果不存在，显示 "使用eBay登录" 的按钮。

### **里程碑三：集成Feed API与异步任务处理 (M3: Feed API & Async Task)**

**目标:** 在用户授权后，调用Feed API创建一个任务来下载包含所有在线商品的报告，并处理其异步性。

1. **创建报告生成路由 (/generate\_report):**  
   * 此路由需要验证用户是否已登录。  
   * 使用session中存储的访问令牌初始化eBay API。  
   * 调用Feed API的 createFeedTask 方法。  
     * feedType: LMS\_ACTIVE\_INVENTORY\_REPORT  
     * schemaVersion: 1.0  
   * Feed API是**异步**的。调用后会立即返回一个 taskId 和任务状态（如 QUEUED）。  
   * 将 taskId 存储在用户 session 中。  
2. **轮询任务状态 (/report\_status/\<task\_id\>):**  
   * 由于Feed任务可能需要几分钟甚至更长时间，必须采用异步处理方式。  
   * 创建一个API端点，让前端页面通过JavaScript (AJAX) 定期调用它来查询任务状态。  
   * 此端点使用 taskId 调用 getFeedTask 方法，获取最新的任务 status (QUEUED, IN\_PROGRESS, COMPLETED, FAILED)。  
3. **下载报告文件 (/download\_report/\<task\_id\>):**  
   * 当 /report\_status 接口返回 COMPLETED 时，前端界面会引导用户访问此路由。  
   * 后端使用 taskId 调用 getFeedResultFile 方法。  
   * 此API调用会返回报告文件（通常是.gz压缩的JSON Lines文件）。  
   * 后端下载并解压该文件，准备进行下一步的数据处理。

### **里程碑四：数据处理与CSV格式转换 (M4: Data Processing & CSV Transformation)**

**目标:** 解析下载的报告文件，提取关键信息，并将其转换为符合File Exchange格式的CSV文件。

1. **安装pandas:**  
   * 在 requirements.txt 中添加 pandas。  
2. **File Exchange格式定义:**  
   * 我们需要生成的CSV文件至少包含以下列，以便于卖家修订Item Specifics：  
     * Action: 固定值为 Revise。  
     * ItemID: 刊登的唯一ID。  
     * C:Brand, C:Size, C:Color, ...: 每一个Item Specific都作为单独的一列，并以 C: 为前缀。这是当前推荐的结构化格式。  
3. **数据转换逻辑:**  
   * 使用 pandas 读取解压后的JSON Lines文件。  
   * 初始化一个空的列表，用于存储每一行的数据（字典格式）。  
   * 遍历报告中的每一个商品记录：  
     * 创建一个字典代表CSV中的一行，并添加'Action': 'Revise'和'ItemID': item\['itemId'\]。  
     * 遍历该商品的 itemSpecifics 数组。对于每一个Specific（例如 {"name": "Brand", "values": \["Nike"\]}），将其转换为字典的键值对：'C:Brand': 'Nike'。  
     * 将处理完的商品字典追加到列表中。  
   * 使用 pd.DataFrame(list\_of\_dicts) 将列表转换为Pandas DataFrame。Pandas会自动处理所有商品中出现过的Specific，并创建对应的列，如果某个商品没有某个Specific，其单元格将为空值。  
4. **CSV文件生成与下载:**  
   * 将最终的DataFrame使用 df.to\_csv(index=False) 转换为CSV格式的字符串。  
   * 创建一个Flask路由（例如 /get\_csv\_file），将此CSV字符串作为HTTP响应返回，并设置正确的HTTP Headers，以触发浏览器下载：  
     * Content-Disposition: attachment; filename="ebay\_item\_specifics.csv"  
     * Content-Type: text/csv

### **里程碑五：前端交互与部署优化 (M5: Frontend & Deployment Optimization)**

**目标:** 创建一个简洁易用的前端界面，并对Cloud Run部署进行最终配置和优化。

1. **前端界面 (使用Flask Templates 和原生JavaScript):**  
   * templates/index.html: 主页，包含登录按钮。  
   * templates/dashboard.html: 登录后页面，包含“生成报告”按钮和一个用于实时显示任务状态的区域（例如 "正在排队...", "处理中...", "已完成, 请点击下载"）。  
   * static/app.js: 使用 fetch API 来：  
     * 请求 /generate\_report 启动任务。  
     * 使用 setInterval 定期轮询 /report\_status。  
     * 根据返回的状态更新页面UI，并在任务完成后显示下载链接。  
2. **Cloud Run 优化配置 (service.yaml):**  
   * **内存/CPU**: pandas处理大型CSV文件时可能会消耗较多内存。根据卖家刊登数量的预估，将内存设置为 1Gi 或更高。  
   * **超时设置**: 适当增加Cloud Run实例的请求超时时间，以应对大型报告的处理。  
   * **环境变量**: 将所有非敏感配置（如应用名称）也设置为环境变量。  
3. **最终测试与部署:**  
   * 在eBay开发者后台，将应用的Redirect URI更新为最终的Cloud Run服务URL。  
   * 执行 gcloud run deploy 进行最终部署。  
   * 进行完整的端到端测试：登录 \-\> 生成报告 \-\> 等待状态更新 \-\> 下载CSV \-\> 验证CSV文件格式和内容的正确性。

## **3\. 项目文件结构建议**

/ebay-spec-exporter  
|-- app.py             \# Flask应用主文件，包含所有路由和逻辑  
|-- requirements.txt   \# Python依赖项  
|-- Dockerfile         \# 容器化配置  
|-- static/            \# 存放前端静态文件  
|   \`-- app.js         \# 前端JavaScript逻辑  
|-- templates/         \# 存放HTML模板  
|   |-- index.html     \# 登录页面  
|   \`-- dashboard.html \# 操作主页面  
\`-- .gcloudignore      \# 忽略不需要上传到Cloud Build的文件

通过遵循以上计划，您可以系统化地、快速地构建一个功能完备、安全且可扩展的工具，并成功地将其部署在Google Cloud Run上。