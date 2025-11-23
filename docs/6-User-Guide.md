---
id: user-guide
sidebar_position: 6
title: User Guide
description: Complete User Guide for Data Extractor MCP Server
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - User Guide
  - MCP Server
  - API Usage
  - Configuration
  - Authentication
---

本文档为 Data Extractor MCP Server 的完整用户使用指南，涵盖了 MCP Server 的所有用法、配置、部署、架构设计以及 API 使用方法。

## 概述

Data Extractor 是一个基于 FastMCP 和 Scrapy、markdownify、pypdf、pymupdf 联合构建的强大、稳定的网页内容、PDF 内容提取 MCP Server，具备转换 Web Page、PDF Document 为 Markdown 的能力，专为商业环境中的长期使用而设计。

### 核心特性

- **14 个专业 MCP 工具**：涵盖网页抓取、PDF 转换、链接提取、表单自动化等
- **多种抓取方法**：支持 simple、scrapy、selenium、playwright 等方法，智能选择最佳策略
- **反检测能力**：隐身抓取和表单自动化功能，绕过反爬虫检测
- **智能内容处理**：自动识别主要内容、格式化 Markdown，支持 8 种格式化选项
- **PDF 深度处理**：图像、表格、数学公式提取，支持增强内容处理
- **企业级特性**：速率限制、缓存、重试、监控、代理支持、错误处理

## 快速开始

### 系统要求

- **Python**: 3.12+
- **操作系统**: Windows, macOS, Linux
- **浏览器**: Chrome/Chromium (Selenium/Playwright 功能)
- **内存**: 建议 2GB+
- **网络**: 稳定的互联网连接

### 安装启动

**方法一：从源码安装**

```bash
# 1. 克隆仓库
git clone https://github.com/ThreeFish-AI/data-extractor.git
cd data-extractor

# 2. 快速设置（推荐）
./scripts/setup.sh

# 3. 或手动安装
# 使用 uv 安装依赖
uv sync

# 4. 安装包括开发依赖（可选）
uv sync --extra dev

# 5. 运行服务器
uv run data-extractor
```

**方法二：从 GitHub 直接安装（推荐生产环境）**

```bash
# 直接安装并运行
uvx --with git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.5 data-extractor
```

**方法三：使用 pip 安装（WIP）**

```bash
# 从 PyPI 安装（如果已发布）
pip install data-extractor
```

**方法四：使用命令**

```bash
# 使用命令行
data-extractor

# 使用 uv 运行（推荐）
uv run data-extractor

# 或者使用Python
python -m extractor.server

# 使用 uv 运行 Python 模块
uv run python -m extractor.server

# 查看当前版本
data-extractor --version

# 查看帮助信息
data-extractor --help
```

### 配置环境

创建 `.env` 文件来自定义配置：

```bash
# 服务器基础配置
DATA_EXTRACTOR_SERVER_NAME=data-extractor
DATA_EXTRACTOR_CONCURRENT_REQUESTS=16
DATA_EXTRACTOR_DOWNLOAD_DELAY=1.0
DATA_EXTRACTOR_RANDOMIZE_DOWNLOAD_DELAY=true

# 浏览器和JavaScript配置
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
DATA_EXTRACTOR_BROWSER_HEADLESS=true
DATA_EXTRACTOR_BROWSER_TIMEOUT=30
DATA_EXTRACTOR_BROWSER_WINDOW_SIZE=1920x1080

# 反检测和代理配置
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true
DATA_EXTRACTOR_USE_PROXY=false
DATA_EXTRACTOR_PROXY_URL=

# 重试和超时配置
DATA_EXTRACTOR_MAX_RETRIES=3
DATA_EXTRACTOR_RETRY_DELAY=1.0
DATA_EXTRACTOR_REQUEST_TIMEOUT=30

# 缓存配置
DATA_EXTRACTOR_ENABLE_CACHING=true
DATA_EXTRACTOR_CACHE_TTL_HOURS=24
DATA_EXTRACTOR_CACHE_MAX_SIZE=1000

# 速率限制
DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# 日志配置
DATA_EXTRACTOR_LOG_LEVEL=INFO
DATA_EXTRACTOR_LOG_REQUESTS=false
DATA_EXTRACTOR_LOG_RESPONSES=false
```

### 验证安装

```bash
# 检查服务器是否正常运行
curl http://localhost:3000/health

# 检查工具列表
curl http://localhost:3000/tools
```

### 更新和升级

```bash
# 从源码更新
git pull origin main
uv sync

# 从 PyPI 更新
pip install --upgrade data-extractor
```

## MCP Server 配置

在您的 MCP Client (如 Claude Desktop) 中添加服务器配置：

### 方式一：直接命令方式

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

### 方式二：通过 uv 启动（推荐）

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

### 方式三：从 GitHub 仓库直接安装和运行（推荐用于生产环境）

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.5",
        "data-extractor"
      ]
    }
  }
}
```

### 方式四：Python 模块方式（本地开发）

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

### Claude Desktop 配置示例

在 Claude Desktop 的 `claude_desktop_config.json` 文件中添加：

```json
{
  "mcpServers": {
    "data-extractor": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.5",
        "data-extractor"
      ],
      "cwd": "/path/to/data-extractor",
      "env": {
        "DATA_EXTRACTOR_ENABLE_JAVASCRIPT": "true",
        "DATA_EXTRACTOR_CONCURRENT_REQUESTS": "8"
      }
    }
  }
}
```

**注意事项：**

- 将 `cwd` 路径替换为您的项目实际路径
- GitHub 仓库地址：`https://github.com/ThreeFish-AI/data-extractor.git`
- 推荐使用方式二（本地 uv 启动）进行开发，方式三（GitHub 直接安装）用于生产环境
- 当前最新稳定版本：v0.1.5

## MCP 工具详细

### 1. scrape_webpage - 基础网页抓取

**功能描述**：抓取单个网页内容，支持多种抓取方法和自定义数据提取配置

**参数**：

- `url` (required): 目标网页 URL
- `method` (optional): 抓取方法，默认 "auto"
- `extract_config` (optional): 数据提取配置
- `wait_for_element` (optional): 等待的 CSS 选择器

**抓取方法选择**：

- `auto`: 智能选择最佳方法
- `simple`: 快速 HTTP 请求，适合静态网页
- `scrapy`: Scrapy 框架，适合复杂页面
- `selenium`: 浏览器渲染，支持 JavaScript

**基础使用示例**：

```json
{
  "url": "https://example.com",
  "method": "auto"
}
```

**高级数据提取示例**：

```json
{
  "url": "https://news.example.com",
  "method": "auto",
  "extract_config": {
    "title": "h1",
    "content": {
      "selector": ".article-content p",
      "multiple": true,
      "attr": "text"
    },
    "author": {
      "selector": ".author",
      "multiple": false,
      "attr": "text"
    },
    "publish_date": {
      "selector": "time",
      "multiple": false,
      "attr": "datetime"
    }
  }
}
```

**返回结果结构**：

```json
{
  "success": true,
  "url": "https://example.com",
  "method": "auto",
  "data": {
    "title": "网页标题",
    "content": ["段落1", "段落2"],
    "author": "作者名称",
    "publish_date": "2025-01-15T10:30:00"
  },
  "metadata": {
    "status_code": 200,
    "content_type": "text/html",
    "response_time": 1.23
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### 2. scrape_multiple_webpages - 批量网页抓取

**功能描述**：并发抓取多个网页，提高处理效率

**参数**：

- `urls` (required): URL 列表
- `method` (optional): 统一抓取方法
- `extract_config` (optional): 全局数据提取配置

**使用示例**：

```json
{
  "urls": [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
  ],
  "method": "simple",
  "extract_config": {
    "title": "h1",
    "description": "meta[name='description']"
  }
}
```

**返回结果**：

```json
{
  "success": true,
  "total_urls": 3,
  "successful_count": 3,
  "failed_count": 0,
  "results": [
    {
      "url": "https://example1.com",
      "success": true,
      "data": { "title": "网站1标题" }
    },
    {
      "url": "https://example2.com",
      "success": true,
      "data": { "title": "网站2标题" }
    },
    {
      "url": "https://example3.com",
      "success": true,
      "data": { "title": "网站3标题" }
    }
  ],
  "summary": {
    "total_processing_time": 5.67,
    "average_response_time": 1.89
  }
}
```

### 3. scrape_with_stealth - 反检测抓取

**功能描述**：使用高级反检测技术抓取有防护的网站

**参数**：

- `url` (required): 目标 URL
- `method` (optional): 反检测方法，默认 "selenium"
- `extract_config` (optional): 数据提取配置
- `wait_for_element` (optional): 等待元素
- `scroll_page` (optional): 是否滚动页面

**反检测特性**：

- 随机 User-Agent 轮换
- 人类行为模拟
- 浏览器指纹隐藏
- IP 代理支持

**使用示例**：

```json
{
  "url": "https://protected-website.com",
  "method": "selenium",
  "scroll_page": true,
  "wait_for_element": ".dynamic-content",
  "extract_config": {
    "content": {
      "selector": ".protected-content",
      "multiple": true,
      "attr": "text"
    }
  }
}
```

### 4. fill_and_submit_form - 表单自动化

**功能描述**：自动填写和提交网页表单

**参数**：

- `url` (required): 包含表单的页面 URL
- `form_data` (required): 表单字段数据
- `submit` (optional): 是否提交，默认 false
- `submit_button_selector` (optional): 提交按钮选择器
- `method` (optional): 自动化方法

**表单字段配置**：

```json
{
  "url": "https://example.com/contact",
  "form_data": {
    "input[name='name']": "张三",
    "input[name='email']": "zhangsan@example.com",
    "input[type='tel']": "13800138000",
    "select[name='country']": "China",
    "input[value='agree']": true,
    "textarea[name='message']": "这是一条测试消息"
  },
  "submit": true,
  "submit_button_selector": "button[type='submit']",
  "method": "selenium"
}
```

**支持的表单元素**：

- `input[type='text']`: 文本输入框
- `input[type='email']`: 邮箱输入框
- `input[type='password']`: 密码输入框
- `input[type='tel']`: 电话输入框
- `select`: 下拉选择框
- `textarea`: 多行文本框
- `input[type='checkbox']`: 复选框
- `input[type='radio']`: 单选按钮

### 5. extract_links - 专业链接提取

**功能描述**：专门用于提取网页中的链接，支持过滤和分类

**参数**：

- `url` (required): 目标网页 URL
- `filter_domains` (optional): 只包含指定域名的链接
- `exclude_domains` (optional): 排除指定域名的链接
- `internal_only` (optional): 只提取内部链接

**基础使用**：

```json
{
  "url": "https://example.com",
  "internal_only": true
}
```

**高级过滤**：

```json
{
  "url": "https://news.example.com",
  "filter_domains": ["news.example.com", "blog.example.com"],
  "exclude_domains": ["ads.example.com", "tracker.example.com"],
  "internal_only": false
}
```

**返回结果**：

```json
{
  "success": true,
  "url": "https://example.com",
  "total_links": 45,
  "internal_links_count": 32,
  "external_links_count": 13,
  "links": [
    {
      "url": "https://example.com/about",
      "text": "关于我们",
      "type": "internal"
    },
    {
      "url": "https://partner.com",
      "text": "合作伙伴",
      "type": "external"
    }
  ]
}
```

### 6. extract_structured_data - 结构化数据提取

**功能描述**：自动识别和提取网页中的结构化数据

**参数**：

- `url` (required): 目标 URL
- `data_type` (optional): 数据类型，默认 "all"

**数据类型选择**：

- `all`: 提取所有类型数据
- `contact`: 仅提取联系方式
- `social`: 仅提取社交媒体链接
- `content`: 仅提取文章内容
- `products`: 仅提取产品信息
- `addresses`: 仅提取地址信息

**使用示例**：

```json
{
  "url": "https://company.com/contact",
  "data_type": "contact"
}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "emails": ["info@company.com", "support@company.com"],
    "phone_numbers": ["+86-10-12345678", "+1-555-0123"],
    "addresses": ["北京市朝阳区xxx街道xxx号"],
    "social_media": [
      { "platform": "twitter", "url": "https://twitter.com/company" },
      { "platform": "linkedin", "url": "https://linkedin.com/company/company" }
    ]
  }
}
```

### 7. get_page_info - 页面基础信息

**功能描述**：快速获取网页的基础元数据信息

**参数**：

- `url` (required): 目标 URL

**使用示例**：

```json
{
  "url": "https://example.com"
}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Website",
    "description": "This is an example website",
    "keywords": ["example", "website", "demo"],
    "status_code": 200,
    "content_type": "text/html",
    "content_length": 15420,
    "last_modified": "2025-01-15T10:00:00Z",
    "response_time": 0.856
  }
}
```

### 8. check_robots_txt - 爬虫规则检查

**功能描述**：检查网站的 robots.txt 文件，确认爬取规则

**参数**：

- `url` (required): 网站域名 URL

**使用示例**：

```json
{
  "url": "https://example.com"
}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "robots_txt_exists": true,
    "can_crawl": true,
    "allowed_paths": ["/public", "/articles"],
    "disallowed_paths": ["/admin", "/private"],
    "crawl_delay": 1.0,
    "sitemap_url": "https://example.com/sitemap.xml"
  }
}
```

### 9. convert_webpage_to_markdown - 网页转 Markdown

**功能描述**：将网页内容转换为结构化的 Markdown 格式

**参数**：

- `url` (required): 目标网页 URL
- `method` (optional): 抓取方法，默认 "auto"
- `extract_main_content` (optional): 是否仅提取主要内容，默认 true
- `include_metadata` (optional): 是否包含元数据，默认 true
- `formatting_options` (optional): 高级格式化选项
- `embed_images` (optional): 是否嵌入图片，默认 false
- `embed_options` (optional): 图片嵌入配置

**高级格式化选项**：

```json
{
  "format_tables": true,
  "detect_code_language": true,
  "format_quotes": true,
  "enhance_images": true,
  "optimize_links": true,
  "format_lists": true,
  "format_headings": true,
  "apply_typography": true
}
```

**图片嵌入配置**：

```json
{
  "max_images": 50,
  "max_bytes_per_image": 2000000,
  "timeout_seconds": 10
}
```

**完整使用示例**：

```json
{
  "url": "https://example.com/article",
  "method": "auto",
  "extract_main_content": true,
  "include_metadata": true,
  "formatting_options": {
    "format_tables": true,
    "detect_code_language": true,
    "apply_typography": true
  },
  "embed_images": true,
  "embed_options": {
    "max_images": 10,
    "max_bytes_per_image": 1500000
  }
}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "url": "https://example.com/article",
    "markdown": "# 文章标题\n\n这是文章的主要内容...",
    "metadata": {
      "title": "文章标题",
      "description": "文章描述",
      "word_count": 1250,
      "character_count": 7500,
      "domain": "example.com",
      "images_embedded": 3
    }
  }
}
```

### 10. batch_convert_webpages_to_markdown - 批量网页转 Markdown

**功能描述**：批量将多个网页转换为 Markdown 格式

**参数**：

- `urls` (required): URL 列表
- `method` (optional): 抓取方法
- `extract_main_content` (optional): 是否仅提取主要内容
- `include_metadata` (optional): 是否包含元数据
- `formatting_options` (optional): 格式化选项
- `embed_images` (optional): 是否嵌入图片
- `embed_options` (optional): 图片嵌入配置

**使用示例**：

```json
{
  "urls": [
    "https://blog.example.com/post1",
    "https://blog.example.com/post2",
    "https://blog.example.com/post3"
  ],
  "method": "auto",
  "extract_main_content": true,
  "formatting_options": {
    "format_tables": true,
    "detect_code_language": true
  }
}
```

### 11. convert_pdf_to_markdown - PDF 转 Markdown

**功能描述**：将 PDF 文档转换为 Markdown 格式，支持增强功能

**参数**：

- `pdf_source` (required): PDF 文件 URL 或本地路径
- `method` (optional): 提取方法，默认 "auto"
- `page_range` (optional): 页面范围 [start, end]
- `output_format` (optional): 输出格式，默认 "markdown"
- `include_metadata` (optional): 是否包含元数据，默认 true
- `extract_images` (optional): 是否提取图像，默认 true
- `extract_tables` (optional): 是否提取表格，默认 true
- `extract_formulas` (optional): 是否提取数学公式，默认 true
- `embed_images` (optional): 是否嵌入图像，默认 false
- `enhanced_options` (optional): 增强处理选项

**增强处理选项**：

```json
{
  "output_dir": "./extracted_assets",
  "image_size": [800, 600],
  "image_format": "png",
  "image_quality": 90
}
```

**基础使用示例**：

```json
{
  "pdf_source": "https://example.com/document.pdf",
  "method": "auto",
  "output_format": "markdown"
}
```

**启用所有增强功能**：

```json
{
  "pdf_source": "https://example.com/document.pdf",
  "method": "pymupdf",
  "extract_images": true,
  "extract_tables": true,
  "extract_formulas": true,
  "embed_images": false,
  "enhanced_options": {
    "output_dir": "./extracted_assets",
    "image_size": [1200, 900],
    "image_format": "png",
    "image_quality": 95
  }
}
```

**页面范围提取**：

```json
{
  "pdf_source": "/path/to/document.pdf",
  "page_range": [0, 10],
  "extract_tables": true
}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "text": "原始提取的文本内容",
    "markdown": "# 文档标题\n\n转换后的 Markdown 内容...",
    "metadata": {
      "title": "文档标题",
      "author": "作者姓名",
      "total_pages": 50,
      "pages_processed": 10,
      "file_size_bytes": 1024000
    },
    "enhanced_assets": {
      "images": {
        "count": 5,
        "files": ["img_0_0_001.png", "img_0_0_002.png"],
        "total_size_mb": 2.4
      },
      "tables": {
        "count": 3,
        "total_rows": 15,
        "total_columns": 8
      },
      "formulas": {
        "count": 8,
        "inline_count": 5,
        "block_count": 3
      }
    }
  }
}
```

### 12. batch_convert_pdfs_to_markdown - 批量 PDF 转 Markdown

**功能描述**：批量转换多个 PDF 文档为 Markdown 格式

**参数**：

- `pdf_sources` (required): PDF 文件列表（URL 或路径）
- `method` (optional): 提取方法，默认 "auto"
- `page_range` (optional): 页面范围，应用于所有 PDF
- `output_format` (optional): 输出格式，默认 "markdown"
- `include_metadata` (optional): 是否包含元数据

**使用示例**：

```json
{
  "pdf_sources": [
    "https://example.com/doc1.pdf",
    "/path/to/doc2.pdf",
    "https://example.com/doc3.pdf"
  ],
  "method": "auto",
  "output_format": "markdown"
}
```

### 13. get_server_metrics - 服务器性能监控

**功能描述**：获取服务器的性能指标和运行统计信息

**参数**：无

**使用示例**：

```json
{}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "total_requests": 1250,
    "successful_requests": 1180,
    "failed_requests": 70,
    "success_rate": 0.944,
    "average_response_time": 2.34,
    "uptime_seconds": 86400,
    "cache_stats": {
      "cache_size": 156,
      "cache_hits": 890,
      "cache_misses": 360,
      "hit_rate": 0.712
    },
    "method_usage": {
      "simple": 450,
      "scrapy": 320,
      "selenium": 280,
      "auto": 200
    },
    "error_distribution": {
      "timeout": 25,
      "connection": 20,
      "parsing": 15,
      "other": 10
    }
  }
}
```

### 14. clear_cache - 缓存管理

**功能描述**：清空服务器的缓存数据

**参数**：无

**使用示例**：

```json
{}
```

**返回结果**：

```json
{
  "success": true,
  "data": {
    "cleared_items": 156,
    "cache_size_before": 156,
    "cache_size_after": 0,
    "operation_time": 0.123,
    "message": "Successfully cleared all cache items"
  }
}
```

## API 编程接口

虽然主要通过 MCP 协议使用，但也支持直接 Python 调用：

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

#### 通过 MCP 协议调用工具

```python
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
```

## 配置详解

数据提取配置使用 JSON 格式，支持简单选择器和高级配置两种方式：

### 简单选择器配置

```json
{
  "title": "h1",
  "content": ".article-content",
  "links": "a",
  "description": "meta[name='description']"
}
```

### 高级配置格式

```json
{
  "field_name": {
    "selector": "CSS选择器",
    "multiple": true/false,  // 是否提取多个元素
    "attr": "text/属性名"     // 提取的属性类型
  }
}
```

**属性类型说明**：

- `text`: 提取元素的文本内容
- `href`: 提取链接 URL
- `src`: 提取图片/媒体源
- `datetime`: 提取时间日期
- `content`: 提取自定义属性内容
- `outerHTML`: 提取完整的 HTML 元素

### 预设配置模板

项目提供了 10 种常用网站类型的预设配置：

**1. 电商网站配置**

```json
{
  "product_name": {
    "selector": "h1.product-title, .product-name h1",
    "attr": "text",
    "multiple": false
  },
  "price": {
    "selector": ".price, .product-price",
    "attr": "text",
    "multiple": false
  },
  "description": {
    "selector": ".product-description, .description",
    "attr": "text",
    "multiple": false
  },
  "images": {
    "selector": ".product-image img, .gallery img",
    "attr": "src",
    "multiple": true
  }
}
```

**2. 新闻文章配置**

```json
{
  "headline": {
    "selector": "h1, .headline, .article-title",
    "attr": "text",
    "multiple": false
  },
  "author": {
    "selector": ".author, .byline, [rel='author']",
    "attr": "text",
    "multiple": false
  },
  "article_body": {
    "selector": ".article-body p, .content p",
    "attr": "text",
    "multiple": true
  }
}
```

**3. 社交媒体配置**

```json
{
  "username": {
    "selector": ".username, .handle, .profile-username",
    "attr": "text",
    "multiple": false
  },
  "display_name": {
    "selector": ".display-name, .profile-name, h1",
    "attr": "text",
    "multiple": false
  },
  "bio": {
    "selector": ".bio, .description, .profile-description",
    "attr": "text",
    "multiple": false
  }
}
```

## 使用技巧

### 1. 智能方法选择

Data Extractor 支持自动选择最适合的抓取方法：

```json
{
  "url": "https://example.com",
  "method": "auto"
}
```

**选择逻辑**：

- 首先尝试 `simple` 方法（最快）
- 如果检测到 JavaScript 需求，升级到 `selenium`
- 如果遇到反爬措施，使用 `stealth` 模式

### 2. 并发处理优化

批量处理时合理设置并发数量：

```json
{
  "urls": ["url1", "url2", "url3"],
  "concurrent_limit": 5,
  "delay_between_requests": 1.0
}
```

### 3. 错误处理策略

实现完整的错误处理和重试机制：

```json
{
  "url": "https://example.com",
  "max_retries": 3,
  "retry_delay": 2.0,
  "timeout": 30.0,
  "fallback_methods": ["simple", "scrapy", "selenium"]
}
```

### 4. 缓存策略

合理使用缓存提升性能：

```json
{
  "cache_enabled": true,
  "cache_ttl": 3600,
  "cache_key_pattern": "{url}_{method}_{config_hash}"
}
```

## 高级使用场景

### 1. 电商数据抓取

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

### 2. 新闻监控系统

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

### 3. 合规性检查流程

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

### 4. 学术论文处理

```python
async def academic_paper_processing():
    # 批量处理学术论文PDF
    pdf_sources = [
        "paper1.pdf",
        "paper2.pdf",
        "paper3.pdf"
    ]

    results = await batch_convert_pdfs_to_markdown(
        pdf_sources=pdf_sources,
        method="pymupdf",
        extract_formulas=True,
        extract_images=True,
        extract_tables=True,
        output_format="markdown"
    )

    return results
```

### 5. 技术文档转换

```python
async def technical_docs_conversion():
    # 将技术文档PDF转换为结构化Markdown
    result = await convert_pdf_to_markdown(
        pdf_source="technical_manual.pdf",
        extract_images=True,
        extract_tables=True,
        embed_images=True,
        enhanced_options={
            "output_dir": "./extracted_assets",
            "image_size": [1200, 900]
        }
    )

    return result
```

## 常见问题

### 1. 连接超时

**问题**：请求经常超时

**解决方案**：

```bash
# 增加超时时间
DATA_EXTRACTOR_REQUEST_TIMEOUT=60

# 使用更稳定的抓取方法
{
  "url": "https://example.com",
  "method": "simple"
}
```

### 2. JavaScript 内容无法抓取

**问题**：动态内容无法提取

**解决方案**：

```bash
# 启用 JavaScript 支持
DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true

# 使用浏览器方法
{
  "url": "https://example.com",
  "method": "selenium",
  "wait_for_element": ".dynamic-content"
}
```

### 3. 反爬虫检测

**问题**：被网站反爬虫系统识别

**解决方案**：

```json
{
  "url": "https://protected-site.com",
  "method": "selenium",
  "use_stealth": true,
  "random_user_agent": true,
  "scroll_page": true
}
```

### 4. 内存不足

**问题**：处理大量数据时内存不足

**解决方案**：

```bash
# 减少并发数量
DATA_EXTRACTOR_CONCURRENT_REQUESTS=3

# 启用缓存清理
DATA_EXTRACTOR_ENABLE_CACHING=false
```

## 最佳实践

### 1. 选择合适的抓取方法

| 网站类型        | 推荐方法 | 原因                 |
| --------------- | -------- | -------------------- |
| 静态网页        | simple   | 速度最快，资源消耗低 |
| JavaScript 网站 | selenium | 支持动态内容渲染     |
| 大规模抓取      | scrapy   | 内置并发和管道处理   |
| 有反爬保护      | stealth  | 避免被检测和封禁     |

### 2. 数据提取策略

- **从小开始**：先测试简单的选择器
- **逐步复杂化**：在基础成功后增加复杂配置
- **错误容忍**：设计容错的数据提取逻辑
- **性能考虑**：避免过于复杂的 CSS 选择器

### 3. 合规使用

- **尊重 robots.txt**：遵守网站的爬虫规则
- **合理频率**：设置适当的请求间隔
- **身份标识**：使用明确的 User-Agent
- **数据用途**：合法使用抓取的数据

### 4. 监控和维护

- **定期检查**：监控服务器性能和错误率
- **缓存管理**：定期清理过期缓存
- **日志分析**：分析请求模式和错误原因
- **版本更新**：保持软件和依赖的更新

## 安全和合规

### 1. 遵守 robots.txt

在使用任何抓取工具前，先检查网站的爬虫规则：

```json
{
  "url": "https://example.com"
}
```

### 2. 设置合理的请求频率

```bash
# 设置请求延迟
DATA_EXTRACTOR_DOWNLOAD_DELAY=2.0

# 限制并发请求数
DATA_EXTRACTOR_CONCURRENT_REQUESTS=5

# 设置速率限制
DATA_EXTRACTOR_RATE_LIMIT_REQUESTS_PER_MINUTE=30
```

### 3. 使用代理和用户代理轮换

```bash
# 启用随机用户代理
DATA_EXTRACTOR_USE_RANDOM_USER_AGENT=true

# 配置代理
DATA_EXTRACTOR_USE_PROXY=true
DATA_EXTRACTOR_PROXY_URL=http://proxy-server:8080
```

### 4. 数据隐私保护

- 不记录敏感信息（密码、个人信息等）
- 遵守数据保护法规（GDPR、CCPA 等）
- 合理存储和处理抓取的数据

## 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/ThreeFish-AI/data-extractor/issues)
- **文档参考**: 查看 `docs/` 目录下的详细文档
- **示例代码**: 查看 `examples/` 目录下的使用示例

---

通过遵循本用户指南，您可以充分利用 Data Extractor MCP Server 的强大功能，高效地进行网页数据提取和文档转换工作。如有任何问题，请参考故障排除部分或联系技术支持。
