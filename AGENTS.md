---
id: agents
sidebar_position: 1
title: AGENTS
description: General Principles for Agents Development
last_update:
  author: Aurelius
  date: 2025-11-20
tags:
  - AGENTS
  - General Principles
  - Development
---

本文档为 Vibe Coding Agents（如 Claude Code、Gemini Cli、CodeX、Cursor 等）提供 Data Extractor 项目的开发总则与使用指导。Data Extractor 包含各种 MCP (Model Context Protocol) 工具，文档包含了 Vibe Coding 在维护 Data Extractor 项目时应当遵循的基本规则与标准，还包含了这些 MCP 工具的功能特性和应用场景介绍。

## 项目概述

Data Extractor 是一个基于 FastMCP 搭建的网页、PDF 文档等转 Markdown 文档的 MCP Server。它基于 Scrapy 构建具备反检测能力的综合网络抓取能力，基于 markitdown、pypdf、pymupdf 等搭建 PDF 文档处理能力，形成专为企业级网页与 PDF 内容抓取与 Markdown 化的一套完整工具。Data Extractor 具备 14 个 MCP 工具，适用于各种文档内容抓取场景。

## 开发命令

### 环境设置和安装

```bash
# 使用提供的脚本快速设置（推荐）
./scripts/setup.sh

# 使用 uv 手动设置
uv sync

# 安装开发依赖
uv sync --extra dev

# 复制环境配置文件
cp .env.example .env
```

### 启动服务器

```bash
# 启动 MCP 服务器（主要命令）
uv run data-extractor

# 备选方案：作为 Python 模块运行
uv run python -m extractor.server

# 使用环境变量运行
uv run --env DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true data-extractor
```

### 代码质量和测试

```bash
# 使用 Black 格式化代码
uv run black extractor/ examples/

# 使用 flake8 进行代码检查
uv run flake8 extractor/

# 使用 mypy 进行类型检查
uv run mypy extractor/

# 运行测试
uv run pytest

# 添加依赖包
uv add <package-name>
uv add --dev <package-name>

# 更新依赖
uv lock --upgrade
```

## 架构概述

### 核心模块结构

系统采用分层架构，以方法自动选择和企业级工具为中心：

**extractor/server.py** - FastMCP 服务器，包含 14 个使用 `@app.tool()` 装饰器的 MCP 工具。每个工具遵循模式：Pydantic 请求模型 → 方法选择 → 错误处理 → 指标收集。

**extractor/scraper.py** - 具有自动方法选择的多策略抓取引擎：

- `WebScraper.scrape_url()` 根据需求协调方法选择
- 支持 Simple HTTP、Scrapy 框架、Selenium 浏览器自动化
- 方法选择逻辑考虑 JavaScript 检测和反爬虫保护需求

**extractor/advanced_features.py** - 隐身能力和表单自动化：

- `AntiDetectionScraper` 使用 undetected-chromedriver 和 Playwright
- `FormHandler` 用于复杂表单交互（下拉框、复选框、文件上传）

**extractor/utils.py** - 支持异步的企业级工具：

- `RateLimiter`、`RetryManager`、`CacheManager`、`MetricsCollector`、`ErrorHandler`
- 所有工具都遵循异步支持、错误处理和指标收集模式

**extractor/config.py** - 使用 `DATA_EXTRACTOR_` 前缀自动环境变量映射的 Pydantic BaseSettings。

**extractor/pdf_processor.py** - PDF 处理引擎，支持 PyMuPDF 和 PyPDF 双引擎，包含增强内容提取功能。

**extractor/markdown_converter.py** - Markdown 转换引擎，支持高级格式化和图片嵌入功能。

### 关键设计模式

**方法自动选择**：`WebScraper` 根据 JavaScript 需求、反爬虫保护和性能需求智能选择抓取方法。

**分层错误处理**：错误在多个级别被捕获，分类（超时、连接、反爬虫），并使用适当的重试策略处理。

**企业级功能**：内置速率限制、带 TTL 的缓存、全面的指标收集和生产部署的代理支持。

## MCP 工具集

### 网页抓取工具

1. **scrape_webpage** - 单页面抓取
2. **scrape_multiple_webpages** - 批量页面抓取
3. **scrape_with_stealth** - 反检测抓取
4. **fill_and_submit_form** - 表单自动化

### 链接和数据提取工具

5. **extract_links** - 专业链接提取
6. **extract_structured_data** - 结构化数据提取
7. **get_page_info** - 页面信息获取
8. **check_robots_txt** - 爬虫规则检查

### Markdown 转换工具

9. **convert_webpage_to_markdown** - 页面转 Markdown
10. **batch_convert_webpages_to_markdown** - 批量页面转 Markdown
11. **convert_pdf_to_markdown** - PDF 转 Markdown（增强功能）
12. **batch_convert_pdfs_to_markdown** - 批量 PDF 转 Markdown

### 服务管理工具

13. **get_server_metrics** - 性能指标监控
14. **clear_cache** - 缓存管理

## 配置系统

环境变量使用 `DATA_EXTRACTOR_` 前缀（参考 .env.example）：

**关键设置：**

- `DATA_EXTRACTOR_ENABLE_JAVASCRIPT` - 全局启用浏览器自动化
- `DATA_EXTRACTOR_USE_RANDOM_USER_AGENT` - 反检测功能
- `DATA_EXTRACTOR_CONCURRENT_REQUESTS` - 控制 Scrapy 并发数
- `DATA_EXTRACTOR_BROWSER_TIMEOUT` - 浏览器等待超时

## 数据提取配置

灵活的提取配置支持简单 CSS 选择器和复杂属性提取：

- 简单配置：`{"title": "h1"}`
- 复杂配置：`{"products": {"selector": ".product", "multiple": true, "attr": "text"}}`
- 属性提取：文本内容、href 链接、src 图片、自定义属性

参考 `examples/extraction_configs.py` 查看涵盖电商、新闻、招聘和房地产场景的综合示例。

## 代码库工作指南

**添加新的 MCP 工具**：在 `server.py` 中使用 `@app.tool()` 装饰器添加。遵循现有模式：Pydantic 请求模型 → 错误处理 → 指标收集。

**扩展抓取方法**：修改 `scraper.py` 中的类。`WebScraper.scrape_url()` 方法协调方法选择逻辑。

**添加反检测功能**：在 `advanced_features.py` 中扩展 `AntiDetectionScraper`。考虑浏览器隐身选项、行为模拟和代理轮换。

**配置更改**：使用 Pydantic Field 和环境变量映射在 `config.py` 中添加设置到 `DataExtractorSettings`。

**工具函数**：按照现有模式添加到 `utils.py`，支持异步、错误处理和指标集成。

## 增强功能特性

### PDF 深度提取

- **图像提取**：从 PDF 页面提取图像元素，支持本地存储或 base64 嵌入
- **表格识别**：智能识别各种格式表格，转换为标准 Markdown 表格
- **数学公式提取**：识别 LaTeX 格式数学公式，保持原始格式完整性
- **结构化输出**：自动生成包含提取资源的结构化 Markdown 文档

### Markdown 高级转换

- **智能内容提取**：自动识别主要内容区域
- **高级格式化**：表格对齐、代码语言检测、智能排版
- **图片嵌入**：支持 data URI 形式嵌入远程图片
- **批量处理**：并发处理多个 URL 或 PDF 文档

## 性能考虑

- 服务器使用 asyncio 进行并发操作
- Scrapy 运行在 Twisted 反应器上（单线程事件循环）
- 浏览器自动化（Selenium/Playwright）资源密集
- 缓存显著提高重复请求性能
- 速率限制防止压垮目标服务器

## 浏览器依赖

Selenium 和隐身功能需要 Chrome/Chromium 浏览器。Playwright 会自动下载自己的浏览器二进制文件。

## 安全注意事项

- 隐身功能应合乎道德地使用
- 始终使用提供的工具检查 robots.txt
- 支持代理功能，但确保使用 HTTPS 代理
- 不记录敏感数据 - 小心处理凭据信息

## 最佳实践

### 负责任的使用

- 尊重网站的使用条款和 robots.txt 规则
- 合理设置请求频率和并发数量
- 避免对目标服务器造成过大负载
- 仅用于合法的数据收集目的

### 错误处理和重试

- 利用内置的重试机制处理网络错误
- 监控性能指标调整配置参数
- 使用缓存减少重复请求
- 定期清理临时文件和缓存

### 部署建议

- 生产环境中使用代理池
- 配置适当的速率限制
- 启用全面的日志记录和监控
- 定期更新依赖包和浏览器驱动
