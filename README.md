# Data Extractor

一个基于 Scrapy 和 FastMCP 构建的强大、稳定的网页爬取与数据提取 MCP Server，专为商业环境中的长期使用而设计。

## 🛠️ MCP Server 核心工具

| 工具名称                               | 功能描述           | 使用场景                         |
| -------------------------------------- | ------------------ | -------------------------------- |
| **scrape_webpage**                     | 单页面抓取         | 基础数据提取，支持配置化选择器   |
| **scrape_multiple_webpages**           | 批量页面抓取       | 并发处理多个 URL，提升效率       |
| **scrape_with_stealth**                | 反检测抓取         | 应对反爬虫保护的高难度网站       |
| **fill_and_submit_form**               | 表单自动化         | 登录表单、联系表单等交互操作     |
| **extract_links**                      | 专业链接提取       | 网站地图生成，链接分析           |
| **extract_structured_data**            | 结构化数据提取     | JSON-LD、微数据、Open Graph 解析 |
| **get_page_info**                      | 页面信息获取       | 快速获取标题、状态码、元数据     |
| **check_robots_txt**                   | 爬虫规则检查       | 遵守网站爬取规范，合规性检查     |
| **get_server_metrics**                 | 性能指标监控       | 服务器状态监控，性能调优         |
| **clear_cache**                        | 缓存管理           | 释放内存，清理过期数据           |
| **convert_webpage_to_markdown**        | 页面转 Markdown    | 将网页内容转换为 Markdown 格式   |
| **batch_convert_webpages_to_markdown** | 批量 Markdown 转换 | 批量处理多个网页的 Markdown 转换 |

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

## 📋 项目现状

### 项目结构

```
data-extractor/
├── extractor/                          # 核心引擎模块
│   ├── __init__.py                     # 包初始化
│   ├── server.py                       # FastMCP 服务器与 10 个 MCP 工具
│   ├── scraper.py                      # WebScraper 核心抓取引擎
│   ├── advanced_features.py            # 反检测与表单自动化
│   ├── config.py                       # 配置管理 (DataExtractorSettings)
│   └── utils.py                        # 企业级工具集 (限流、重试、缓存等)
├── examples/                           # 使用示例
│   ├── basic_usage.py                  # 基础用法示例
│   └── extraction_configs.py           # 数据提取配置示例
├── tests/                              # 完整测试体系
│   ├── unit/                           # 单元测试
│   │   ├── test_scraper_simple.py      # WebScraper 基础测试
│   │   ├── test_utils_basic.py         # 工具类测试
│   │   └── test_advanced_features.py   # 高级功能测试
│   ├── integration/                    # 集成测试
│   │   └── test_mcp_tools.py           # 10 个 MCP 工具测试
│   └── conftest.py                     # pytest 配置和 fixtures
├── scripts/
│   └── setup.sh                        # 快速安装脚本
├── TESTING.md                          # 测试文档 (67KB)
├── TEST_RESULTS.md                     # 测试执行报告
├── CHANGELOG.md                        # 版本变更日志
├── CLAUDE.md                           # Claude Code 项目指导
├── .env.example                        # 环境变量配置示例
├── pyproject.toml                      # 项目配置和依赖管理
└── uv.lock                             # 依赖锁定文件
```

### 已完成的里程碑 ✅

- ✅ **v0.1.2 稳定版发布**: 基于 Scrapy + FastMCP 构建的企业级网页抓取 MCP Server
- ✅ **测试框架建设**: 完整的单元测试和集成测试体系，测试通过率 99%+
- ✅ **代码质量优化**: 类型注解完善，从 black 迁移到 ruff 格式化
- ✅ **配置统一**: 项目名称从 scrapy-mcp 更名为 data-extractor，配置前缀统一
- ✅ **文档完善**: README、CHANGELOG、TESTING 文档体系建立

### 当前状态 📊

- **版本**: v0.1.2
- **测试覆盖率**: 99%+
- **代码格式化**: ruff
- **包管理**: uv
- **Python 要求**: 3.12+

### v0.1.2 (2025-09-06)

- **测试框架**: 建立完整的单元测试和集成测试体系，19 个基础测试全部通过
- **测试文档**: 新增 67KB 详细测试文档和执行报告
- **质量保障**: pytest 异步测试支持，Mock 策略和性能优化

### v0.1.1 (2025-09-05)

- **核心重构**: 包名从 `scrapy_mcp` 重构为 `extractor`，提升项目结构清晰度
- **命令更新**: 项目入口命令统一为 `data-extractor`
- **文档完善**: 更新所有配置示例和安装说明

### v0.1.0 (2025-08-26)

- **初始发布**: 完整的网页爬取 MCP Server 实现
- **核心功能**: 10 个专业爬取工具，支持多种场景
- **企业特性**: 速率限制、智能重试、缓存机制
- **技术栈**: 迁移至 uv 包管理，增强开发体验

## 🚦 快速开始

### 📦 安装

```bash
# 确认 Python 版本 (需要 3.12+)
python --version

# 克隆仓库
git clone https://github.com/ThreeFish-AI/data-extractor.git
cd data-extractor

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

### 🔧 配置

创建 `.env` 文件来自定义配置：

```bash
# 服务器设置
DATA_EXTRACTOR_SERVER_NAME=data-extractor
DATA_EXTRACTOR_SERVER_VERSION=0.1.2

# 并发和延迟设置
DATA_EXTRACTOR_CONCURRENT_REQUESTS=16
DATA_EXTRACTOR_DOWNLOAD_DELAY=1.0
DATA_EXTRACTOR_RANDOMIZE_DOWNLOAD_DELAY=true

# 浏览器设置
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_BROWSER_TIMEOUT=30

# 反检测设置
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
DATA_EXTRACTOR_USE_PROXY=false
DATA_EXTRACTOR_PROXY_URL=

# 重试设置
DATA_EXTRACTOR_MAX_RETRIES=3
DATA_EXTRACTOR_REQUEST_TIMEOUT=30
```

### 启动服务器

```bash
# 使用命令行
data-extractor

# 使用 uv 运行（推荐）
uv run data-extractor

# 或者使用Python
python -m extractor.server

# 使用 uv 运行 Python 模块
uv run python -m extractor.server
```

### MCP Client 配置

在您的 MCP client (如 Claude Desktop) 中添加服务器配置：

#### 方式一：直接命令方式

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "data-extractor",
      "args": []
    }
  }
}
```

#### 方式二：通过 uv 启动（推荐）

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "uv",
      "args": ["run", "data-extractor"],
      "cwd": "/path/to/your/data-extractor"
    }
  }
}
```

#### 方式三：从 GitHub 仓库直接安装和运行（推荐用于生产环境）

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.1",
        "data-extractor"
      ]
    }
  }
}
```

#### 方式四：Python 模块方式（本地开发）

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "uv",
      "args": ["run", "python", "-m", "extractor.server"],
      "cwd": "/path/to/your/data-extractor"
    }
  }
}
```

**注意事项：**

- 将 `cwd` 路径替换为您的项目实际路径
- GitHub 仓库地址：`https://github.com/ThreeFish-AI/data-extractor.git`
- 推荐使用方式二（本地 uv 启动）进行开发，方式三（GitHub 直接安装）用于生产环境
- 当前最新稳定版本：v0.1.2

## 🛠️ 工具详情

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

### 11. convert_webpage_to_markdown

将网页内容抓取并转换为 Markdown 格式，适用于文档处理、内容分析和存储。

**参数:**

- `url`: 要抓取和转换的 URL
- `method`: 抓取方法 (auto/simple/scrapy/selenium，默认 auto)
- `extract_main_content`: 是否仅提取主要内容区域 (默认 true)
- `include_metadata`: 是否包含页面元数据 (默认 true)
- `custom_options`: 自定义 Markdown 转换选项 (可选)
- `wait_for_element`: 等待的 CSS 选择器 (Selenium 专用)

**功能特性:**

- **智能内容提取**: 自动识别并提取网页主要内容区域
- **清理处理**: 移除广告、导航栏、侧边栏等无关内容
- **URL 转换**: 将相对 URL 转换为绝对 URL
- **格式优化**: 清理多余空白行，优化 Markdown 格式
- **元数据丰富**: 包含标题、描述、字数统计等信息

**示例:**

```json
{
  "url": "https://example.com/article",
  "method": "auto",
  "extract_main_content": true,
  "include_metadata": true,
  "custom_options": {
    "heading_style": "ATX",
    "bullets": "-",
    "wrap": false
  }
}
```

**返回示例:**

```json
{
  "success": true,
  "data": {
    "url": "https://example.com/article",
    "markdown": "# Article Title\n\nThis is the article content...",
    "metadata": {
      "title": "Article Title",
      "meta_description": "Article description",
      "word_count": 500,
      "character_count": 3000,
      "domain": "example.com"
    }
  }
}
```

### 12. batch_convert_webpages_to_markdown

批量抓取多个网页并转换为 Markdown 格式，支持并发处理提升效率。

**参数:**

- `urls`: 要抓取和转换的 URL 列表
- `method`: 抓取方法 (auto/simple/scrapy/selenium，默认 auto)
- `extract_main_content`: 是否仅提取主要内容区域 (默认 true)
- `include_metadata`: 是否包含页面元数据 (默认 true)
- `custom_options`: 自定义 Markdown 转换选项 (可选)

**功能特性:**

- **并发处理**: 同时处理多个 URL 提升效率
- **一致格式**: 所有页面使用相同的转换配置
- **详细统计**: 提供成功/失败统计和汇总信息
- **错误处理**: 单个页面失败不影响其他页面处理
- **批量优化**: 针对大量页面优化的性能配置

**示例:**

```json
{
  "urls": [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
  ],
  "method": "auto",
  "extract_main_content": true,
  "include_metadata": true
}
```

**返回示例:**

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "success": true,
        "url": "https://example.com/article1",
        "markdown": "# Article 1\n\nContent...",
        "metadata": {...}
      },
      {
        "success": true,
        "url": "https://example.com/article2",
        "markdown": "# Article 2\n\nContent...",
        "metadata": {...}
      }
    ],
    "summary": {
      "total": 3,
      "successful": 2,
      "failed": 1,
      "success_rate": 0.67
    }
  }
}
```

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

## 🏗️ 架构设计

### Data Extractor 核心引擎层

Data Extractor 核心引擎采用分层架构设计，提供稳定可靠的网页抓取能力：

#### 1. WebScraper 主控制器 (`extractor/scraper.py`)

**设计理念**: 统一接口，智能方法选择

```python
class WebScraper:
    """主控制器，协调各种抓取方法"""

    def __init__(self):
        self.scrapy_wrapper = ScrapyWrapper()      # Scrapy 框架封装
        self.selenium_scraper = SeleniumScraper()  # 浏览器自动化
        self.simple_scraper = SimpleScraper()      # HTTP 请求

    async def scrape_url(self, url: str, method: str = "auto",
                         extract_config: Optional[Dict] = None) -> Dict:
        """智能选择最适合的抓取方法"""
```

**核心特性**:

- **方法自选**: 根据 JavaScript 需求和反检测要求自动选择 simple/scrapy/selenium
- **统一接口**: 所有抓取方法通过统一的 `scrape_url()` 接口调用
- **并发支持**: `scrape_multiple_urls()` 实现高效批量处理
- **配置化提取**: 支持 CSS 选择器、属性提取、多元素批量获取

#### 2. 高级功能模块 (`extractor/advanced_features.py`)

**AntiDetectionScraper 反检测引擎**:

```python
class AntiDetectionScraper:
    """反检测专用抓取器"""

    async def scrape_with_stealth(self, url: str, method: str = "selenium"):
        """使用反检测技术抓取"""
        # 支持 undetected-chromedriver 和 Playwright 双引擎
        # 自动注入隐身脚本，模拟人类行为
```

**FormHandler 表单自动化**:

```python
class FormHandler:
    """智能表单处理器"""

    async def fill_and_submit_form(self, url: str, form_data: Dict):
        """自动识别表单元素类型并填写"""
        # 支持 input/select/textarea/checkbox/radio 等所有元素
        # 智能等待和提交策略
```

#### 3. 企业级工具集 (`extractor/utils.py`)

**核心工具类**:

- **RateLimiter**: 请求频率控制，防止服务器过载
- **RetryManager**: 指数退避重试，智能错误恢复
- **CacheManager**: 内存缓存系统，提升重复请求性能
- **MetricsCollector**: 性能指标收集，支持实时监控
- **ErrorHandler**: 错误分类处理，区分网络/超时/反爬等异常

**使用示例**:

```python
from extractor.utils import rate_limiter, retry_manager, cache_manager

# 限流控制
await rate_limiter.wait()

# 智能重试
result = await retry_manager.retry_async(scrape_function)

# 缓存管理
cache_manager.set(url, result, ttl=3600)
```

#### 4. 配置管理系统 (`extractor/config.py`)

**DataExtractorSettings 配置类**:

```python
class DataExtractorSettings(BaseSettings):
    """Pydantic 配置管理"""

    # 服务器配置
    server_name: str = "Data Extractor MCP Server"
    concurrent_requests: int = 16

    # 浏览器配置
    enable_javascript: bool = False
    browser_timeout: int = 30

    # 反检测配置
    use_random_user_agent: bool = False

    model_config = SettingsConfigDict(
        env_prefix="DATA_EXTRACTOR_",  # 环境变量前缀
        env_file=".env"
    )
```

### Data Extractor MCP 工具集

MCP (Model Context Protocol) 工具集基于 FastMCP 框架，提供 10 个专业级网页抓取工具：

#### 1. 服务器架构 (`extractor/server.py`)

**FastMCP 服务器设计**:

```python
from fastmcp import FastMCP

app = FastMCP(settings.server_name, version=settings.server_version)
web_scraper = WebScraper()
anti_detection_scraper = AntiDetectionScraper()

@app.tool()
async def scrape_webpage(url: str, method: str = "auto",
                        extract_config: Optional[Dict] = None) -> Dict:
    """MCP 工具装饰器，自动处理输入验证和错误处理"""
```

#### 2. 核心工具详细实现

**scrape_webpage - 基础抓取工具**:

```python
@app.tool()
async def scrape_webpage(url: str, method: str = "auto",
                        extract_config: Optional[Dict] = None,
                        wait_for_element: Optional[str] = None) -> Dict:
    """
    支持的数据提取配置:
    {
        "title": "h1",                          # 简单选择器
        "products": {                           # 高级配置
            "selector": ".product",
            "multiple": true,
            "attr": "text"
        },
        "links": {
            "selector": "a",
            "multiple": true,
            "attr": "href"
        }
    }
    """
```

**scrape_with_stealth - 反检测工具**:

```python
@app.tool()
async def scrape_with_stealth(url: str, method: str = "selenium",
                             extract_config: Optional[Dict] = None) -> Dict:
    """
    反检测技术:
    - undetected-chromedriver: 绕过 Selenium 检测
    - Playwright stealth: 原生反检测支持
    - 随机 User-Agent: 降低识别风险
    - 人类行为模拟: 鼠标移动、页面滚动
    """
```

**fill_and_submit_form - 表单自动化**:

```python
@app.tool()
async def fill_and_submit_form(url: str, form_data: Dict,
                              submit: bool = False) -> Dict:
    """
    智能表单处理:
    - 自动识别 input/select/textarea/checkbox 元素
    - 支持复杂表单验证和提交
    - 等待页面响应和重定向处理
    """
```

## 🚀 实现与使用指南

### Data Extractor 核心引擎使用方式

#### 1. 直接使用核心引擎

```python
from extractor.scraper import WebScraper
from extractor.advanced_features import AntiDetectionScraper, FormHandler

# 基础抓取
scraper = WebScraper()
result = await scraper.scrape_url("https://example.com", method="simple")

# 反检测抓取
stealth_scraper = AntiDetectionScraper()
result = await stealth_scraper.scrape_with_stealth("https://protected-site.com")

# 表单自动化
form_handler = FormHandler()
result = await form_handler.fill_and_submit_form(
    "https://example.com/contact",
    {"input[name='email']": "test@example.com"}
)
```

#### 2. 配置化数据提取

```python
# 简单配置
extract_config = {
    "title": "h1",
    "content": ".article-content"
}

# 高级配置
extract_config = {
    "products": {
        "selector": ".product-item",
        "multiple": True,
        "attr": "text"
    },
    "prices": {
        "selector": ".price",
        "multiple": True,
        "attr": "data-price"
    },
    "images": {
        "selector": "img.product-image",
        "multiple": True,
        "attr": "src"
    }
}

result = await scraper.scrape_url(url, extract_config=extract_config)
```

#### 3. 企业级功能集成

```python
from extractor.utils import (
    rate_limiter, retry_manager, cache_manager,
    metrics_collector, error_handler
)

# 集成完整功能的抓取流程
async def enterprise_scrape(url: str):
    # 检查缓存
    cached_result = cache_manager.get(url)
    if cached_result:
        return cached_result

    # 速率限制
    await rate_limiter.wait()

    # 重试机制
    try:
        result = await retry_manager.retry_async(
            scraper.scrape_url, url, method="auto"
        )

        # 记录指标
        metrics_collector.record_request("GET", True, 1500, "scraper")

        # 缓存结果
        cache_manager.set(url, result, ttl=3600)

        return result

    except Exception as e:
        error_handler.handle_error(e, "enterprise_scrape")
        raise
```

### Data Extractor MCP 工具集使用方式

#### 1. MCP Client 集成

**通过 Claude Desktop 使用**:

1. 启动 Data Extractor MCP 服务器
2. 在 Claude Desktop 中配置服务器连接
3. 直接调用 MCP 工具进行网页抓取

**示例对话**:

```
用户: 帮我抓取 https://news.ycombinator.com 的标题和链接

Claude: 我来使用 scrape_webpage 工具为您抓取 Hacker News 的内容

工具调用: scrape_webpage
参数: {
  "url": "https://news.ycombinator.com",
  "extract_config": {
    "titles": {
      "selector": ".titleline > a",
      "multiple": true,
      "attr": "text"
    },
    "links": {
      "selector": ".titleline > a",
      "multiple": true,
      "attr": "href"
    }
  }
}
```

#### 2. 编程方式调用 MCP 工具

```python
# 通过 MCP 协议调用工具
import asyncio
from extractor.server import (
    scrape_webpage, scrape_multiple_webpages,
    scrape_with_stealth, fill_and_submit_form
)

# 基础页面抓取
async def basic_scraping_example():
    result = await scrape_webpage(
        url="https://example.com",
        method="auto",
        extract_config={
            "title": "h1",
            "content": ".main-content"
        }
    )
    print(f"页面标题: {result['data']['extracted_data']['title']}")

# 批量抓取
async def batch_scraping_example():
    urls = [
        "https://site1.com",
        "https://site2.com",
        "https://site3.com"
    ]

    results = await scrape_multiple_webpages(
        urls=urls,
        method="simple",
        extract_config={"title": "h1"}
    )

    for result in results['data']:
        print(f"URL: {result['url']}, 标题: {result.get('title', 'N/A')}")

# 反检测抓取
async def stealth_scraping_example():
    result = await scrape_with_stealth(
        url="https://protected-website.com",
        method="playwright",
        extract_config={
            "content": ".protected-content",
            "data": "[data-value]"
        }
    )
    return result

# 表单自动化
async def form_automation_example():
    result = await fill_and_submit_form(
        url="https://example.com/contact",
        form_data={
            "input[name='name']": "John Doe",
            "input[name='email']": "john@example.com",
            "textarea[name='message']": "Hello from Data Extractor!"
        },
        submit=True,
        submit_button_selector="button[type='submit']"
    )
    return result
```

#### 3. 高级使用场景

**电商数据抓取**:

```python
async def ecommerce_scraping():
    # 抓取产品列表
    products_result = await scrape_webpage(
        url="https://shop.example.com/products",
        extract_config={
            "products": {
                "selector": ".product-card",
                "multiple": True,
                "attr": "text"
            },
            "prices": {
                "selector": ".price",
                "multiple": True,
                "attr": "text"
            },
            "product_links": {
                "selector": ".product-card a",
                "multiple": True,
                "attr": "href"
            }
        }
    )

    # 批量抓取产品详情
    product_urls = products_result['data']['extracted_data']['product_links']
    details = await scrape_multiple_webpages(
        urls=product_urls[:10],  # 限制前10个产品
        extract_config={
            "description": ".product-description",
            "specifications": ".specs-table",
            "images": {
                "selector": ".product-images img",
                "multiple": True,
                "attr": "src"
            }
        }
    )

    return {
        "products_overview": products_result,
        "product_details": details
    }
```

**新闻监控系统**:

```python
async def news_monitoring_system():
    news_sites = [
        "https://news.ycombinator.com",
        "https://techcrunch.com",
        "https://arstechnica.com"
    ]

    # 批量抓取新闻标题
    news_results = await scrape_multiple_webpages(
        urls=news_sites,
        extract_config={
            "headlines": {
                "selector": "h1, h2, .headline",
                "multiple": True,
                "attr": "text"
            },
            "timestamps": {
                "selector": ".timestamp, time",
                "multiple": True,
                "attr": "text"
            }
        }
    )

    # 提取所有链接用于深度分析
    all_links = []
    for site in news_sites:
        links_result = await extract_links(
            url=site,
            internal_only=True
        )
        all_links.extend(links_result['data']['links'])

    return {
        "news_headlines": news_results,
        "discovered_links": all_links
    }
```

**合规性检查流程**:

```python
async def compliance_check_workflow(target_url: str):
    # 1. 检查 robots.txt
    robots_result = await check_robots_txt(target_url)

    if not robots_result['data']['can_crawl']:
        return {"error": "网站禁止爬取", "robots_txt": robots_result}

    # 2. 获取页面基础信息
    page_info = await get_page_info(target_url)

    # 3. 执行合规的数据抓取
    scrape_result = await scrape_webpage(
        url=target_url,
        method="simple",  # 使用最轻量的方法
        extract_config={
            "public_content": ".main-content, .article",
            "meta_info": "meta[name='description']"
        }
    )

    # 4. 检查服务器性能影响
    metrics = await get_server_metrics()

    return {
        "compliance_check": robots_result,
        "page_info": page_info,
        "extracted_data": scrape_result,
        "performance_metrics": metrics
    }
```

## 📋 版本管理

### 项目版本维护

项目使用语义化版本控制（Semantic Versioning），版本号格式为 `MAJOR.MINOR.PATCH`：

- **MAJOR**: 重大不兼容变更
- **MINOR**: 新功能增加，向后兼容
- **PATCH**: 错误修复，向后兼容

### 版本升级步骤

1. **更新版本号**

```bash
# 编辑 pyproject.toml 中的 version 字段
vim pyproject.toml
```

2. **更新变更日志**

```bash
# 在 CHANGELOG.md 中记录变更内容
vim CHANGELOG.md
```

3. **更新 README 版本信息**

```bash
# 更新 README.md 中的"当前最新稳定版本"
vim README.md
```

4. **提交版本变更**

```bash
git add pyproject.toml CHANGELOG.md README.md
git commit -m "chore(release): bump version to vX.Y.Z"
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push && git push --tags
```

5. **构建和发布**

```bash
# 使用 uv 构建包
uv build

# 发布到 PyPI（如需要）
uv publish
```

### 版本检查

```bash
# 检查当前版本
python -c "import extractor; print(extractor.__version__)"

# 或使用 uv
uv run python -c "from extractor import __version__; print(__version__)"
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

如遇问题请提交 GitHub Issue 或联系 [@ThreeFish-AI](aureliusshu@gmail.com)。

---

**注意**: 请负责任地使用此工具，遵守网站的使用条款和 robots.txt 规则，尊重网站的知识产权。
