# Scrapy MCP Server

一个基于 Scrapy 和 FastMCP 构建的强大、稳定的网页爬取 MCP Server，专为商业环境中的长期使用而设计。

## 🚀 特性

### 核心功能

- **多种爬取方法**: 支持简单 HTTP 请求、Scrapy 框架和浏览器自动化
- **智能方法选择**: 自动选择最适合的爬取方法
- **并发处理**: 支持多个 URL 的并发爬取
- **配置化提取**: 灵活的数据提取配置系统

### 高级功能

- **反反爬虫**: 使用 undetected-chromedriver 和 Playwright 的隐身技术
- **表单处理**: 自动填写和提交各种类型的表单
- **JavaScript 支持**: 完整的浏览器渲染支持
- **智能重试**: 指数退避重试机制
- **结果缓存**: 内存缓存提升性能

### 企业级特性

- **错误处理**: 完善的错误分类和处理
- **性能监控**: 详细的请求指标和统计
- **速率限制**: 防止服务器过载
- **代理支持**: 支持 HTTP 代理配置
- **随机 UA**: 防检测的用户代理轮换

## 📦 安装

```bash
# 克隆仓库
git clone <repository-url>
cd scrapy-mcp

# 快速设置（推荐）
./scripts/setup.sh

# 或手动安装
# 使用 uv 安装依赖
uv sync

# 安装包括开发依赖
uv sync --extra dev

# 或者使用传统方式
pip install -e .

# 或者使用开发模式
pip install -e ".[dev]"
```

## 🔧 配置

创建 `.env` 文件来自定义配置：

```bash
# 服务器设置
SCRAPY_MCP_SERVER_NAME=scrapy-mcp-server
SCRAPY_MCP_SERVER_VERSION=0.1.0

# 并发和延迟设置
SCRAPY_CONCURRENT_REQUESTS=16
SCRAPY_DOWNLOAD_DELAY=1.0
SCRAPY_RANDOMIZE_DOWNLOAD_DELAY=true

# 浏览器设置
SCRAPY_MCP_ENABLE_JAVASCRIPT=false
SCRAPY_MCP_BROWSER_HEADLESS=true
SCRAPY_MCP_BROWSER_TIMEOUT=30

# 反检测设置
SCRAPY_MCP_USE_RANDOM_USER_AGENT=true
SCRAPY_MCP_USE_PROXY=false
SCRAPY_MCP_PROXY_URL=

# 重试设置
SCRAPY_MCP_MAX_RETRIES=3
SCRAPY_MCP_REQUEST_TIMEOUT=30
```

## 🚦 快速开始

### 启动服务器

```bash
# 使用命令行
scrapy-mcp

# 使用 uv 运行（推荐）
uv run scrapy-mcp

# 或者使用Python
python -m scrapy_mcp.server

# 使用 uv 运行 Python 模块
uv run python -m scrapy_mcp.server
```

### MCP Client 配置

在您的 MCP client (如 Claude Desktop) 中添加服务器配置：

```json
{
  "mcpServers": {
    "scrapy-mcp": {
      "command": "scrapy-mcp",
      "args": []
    }
  }
}
```

## 🛠️ 可用工具

### 1. scrape_webpage

基础网页爬取工具，支持多种方法和自定义提取规则。

**参数:**

- `url`: 要爬取的 URL
- `method`: 爬取方法 (auto/simple/scrapy/selenium)
- `extract_config`: 数据提取配置 (可选)
- `wait_for_element`: 等待的 CSS 选择器 (Selenium 专用)

**示例:**

```json
{
  "url": "https://example.com",
  "method": "auto",
  "extract_config": {
    "title": "h1",
    "content": {
      "selector": ".content p",
      "multiple": true,
      "attr": "text"
    }
  }
}
```

### 2. scrape_multiple_webpages

并发爬取多个网页。

**示例:**

```json
{
  "urls": ["https://example1.com", "https://example2.com"],
  "method": "simple",
  "extract_config": {
    "title": "h1",
    "links": "a"
  }
}
```

### 3. scrape_with_stealth

使用高级反检测技术爬取网页。

**参数:**

- `url`: 目标 URL
- `method`: 隐身方法 (selenium/playwright)
- `extract_config`: 提取配置
- `wait_for_element`: 等待元素
- `scroll_page`: 是否滚动页面加载动态内容

**示例:**

```json
{
  "url": "https://protected-site.com",
  "method": "playwright",
  "scroll_page": true,
  "wait_for_element": ".dynamic-content"
}
```

### 4. fill_and_submit_form

表单填写和提交。

**参数:**

- `url`: 包含表单的页面 URL
- `form_data`: 表单字段数据 (选择器:值 对)
- `submit`: 是否提交表单
- `submit_button_selector`: 提交按钮选择器
- `method`: 方法 (selenium/playwright)

**示例:**

```json
{
  "url": "https://example.com/contact",
  "form_data": {
    "input[name='name']": "John Doe",
    "input[name='email']": "john@example.com",
    "textarea[name='message']": "Hello world"
  },
  "submit": true,
  "method": "selenium"
}
```

### 5. extract_links

专门的链接提取工具。

**参数:**

- `url`: 目标 URL
- `filter_domains`: 只包含这些域名的链接
- `exclude_domains`: 排除这些域名的链接
- `internal_only`: 只提取内部链接

**示例:**

```json
{
  "url": "https://example.com",
  "internal_only": true
}
```

### 6. extract_structured_data

自动提取结构化数据 (联系信息、社交媒体链接等)。

**参数:**

- `url`: 目标 URL
- `data_type`: 数据类型 (all/contact/social/content)

**示例:**

```json
{
  "url": "https://company.com",
  "data_type": "contact"
}
```

### 7. get_page_info

快速获取页面基础信息。

**示例:**

```json
{
  "url": "https://example.com"
}
```

### 8. check_robots_txt

检查网站的 robots.txt 文件。

### 9. get_server_metrics

获取服务器性能指标和统计信息。

### 10. clear_cache

清除缓存的爬取结果。

## 📖 数据提取配置

### 简单选择器

```json
{
  "title": "h1",
  "links": "a"
}
```

### 高级配置

```json
{
  "products": {
    "selector": ".product",
    "multiple": true,
    "attr": "text"
  },
  "prices": {
    "selector": ".price",
    "multiple": true,
    "attr": "data-price"
  },
  "description": {
    "selector": ".description",
    "multiple": false,
    "attr": "text"
  }
}
```

## 🎯 最佳实践

### 1. 选择合适的方法

- **simple**: 静态内容，快速爬取
- **scrapy**: 大规模爬取，需要高级特性
- **selenium**: JavaScript 重度网站
- **stealth**: 有反爬保护的网站

### 2. 遵守网站规则

- 使用 `check_robots_txt` 工具检查爬取规则
- 设置合适的延迟和并发限制
- 尊重网站的使用条款

### 3. 性能优化

- 使用缓存避免重复请求
- 合理设置超时时间
- 监控 `get_server_metrics` 调整配置

### 4. 错误处理

- 实施重试逻辑
- 监控错误类别
- 根据错误类型调整策略

## 🔍 故障排除

### 常见问题

**1. Selenium/Playwright 启动失败**

- 确保安装了 Chrome 浏览器
- 检查系统权限和防火墙设置

**2. 反爬虫检测**

- 使用 `scrape_with_stealth` 工具
- 启用随机 User-Agent
- 配置代理服务器

**3. 超时错误**

- 增加 `browser_timeout` 设置
- 检查网络连接
- 使用更稳定的爬取方法

**4. 内存占用过高**

- 减少并发请求数
- 清理缓存
- 检查是否有资源泄露

## 📊 性能指标

使用 `get_server_metrics` 工具监控：

- 请求总数和成功率
- 平均响应时间
- 错误分类统计
- 方法使用分布
- 缓存命中率

## 🔒 安全注意事项

- 不要在日志中记录敏感信息
- 使用 HTTPS 代理服务器
- 定期更新依赖包
- 遵守数据保护法规

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📞 支持

如遇问题请提交 GitHub Issue 或联系维护团队。

---

**注意**: 请负责任地使用此工具，遵守网站的使用条款和 robots.txt 规则，尊重网站的知识产权。
