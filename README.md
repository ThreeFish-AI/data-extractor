---
id: readme
sidebar_position: 1
title: Readme
description: Engineering Architecture Design Framework
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - FRAMEWORK
  - Architecture
  - Design
  - Engineering
---

Data Extractor 是一个基于 FastMCP 和 Scrapy、markdownify、pypdf、pymupdf 联合构建的强大、稳定的网页内容、PDF 内容提取 MCP Server，具备转换 Web Page、PDF Document 为 Markdown 的能力，专为商业环境中的长期使用而设计。

## 🛠️ MCP Server 核心工具 (14 个)

### 网页抓取工具

| 工具名称                     | 功能描述       | 主要参数                                                                                |
| ---------------------------- | -------------- | --------------------------------------------------------------------------------------- |
| **scrape_webpage**           | 单页面抓取     | `url`, `method`(自动选择), `extract_config`(选择器配置), `wait_for_element`(CSS 选择器) |
| **scrape_multiple_webpages** | 批量页面抓取   | `urls`(列表), `method`(统一方法), `extract_config`(全局配置)                            |
| **scrape_with_stealth**      | 反检测抓取     | `url`, `method`(selenium/playwright), `scroll_page`(滚动加载), `wait_for_element`       |
| **fill_and_submit_form**     | 表单自动化     | `url`, `form_data`(选择器:值), `submit`(是否提交), `submit_button_selector`             |
| **extract_links**            | 专业链接提取   | `url`, `filter_domains`(域名过滤), `exclude_domains`(排除域名), `internal_only`(仅内部) |
| **extract_structured_data**  | 结构化数据提取 | `url`, `data_type`(all/contact/social/content/products/addresses)                       |

### 页面信息工具

| 工具名称             | 功能描述     | 主要参数                                   |
| -------------------- | ------------ | ------------------------------------------ |
| **get_page_info**    | 页面信息获取 | `url`(目标 URL) - 返回标题、状态码、元数据 |
| **check_robots_txt** | 爬虫规则检查 | `url`(域名 URL) - 检查 robots.txt 规则     |

### Markdown 转换工具

| 工具名称                               | 功能描述           | 主要参数                                                                                            |
| -------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **convert_webpage_to_markdown**        | 页面转 Markdown    | `url`, `method`, `extract_main_content`(提取主内容), `embed_images`(嵌入图片), `formatting_options` |
| **batch_convert_webpages_to_markdown** | 批量 Markdown 转换 | `urls`(列表), `method`, `extract_main_content`, `embed_images`, `embed_options`                     |
| **convert_pdf_to_markdown**            | PDF 转 Markdown    | `pdf_source`(URL/路径), `method`(auto/pymupdf/pypdf), `page_range`, `output_format`                 |
| **batch_convert_pdfs_to_markdown**     | 批量 PDF 转换      | `pdf_sources`(列表), `method`, `page_range`, `output_format`, `include_metadata`                    |

### 服务管理工具

| 工具名称               | 功能描述     | 主要参数                                  |
| ---------------------- | ------------ | ----------------------------------------- |
| **get_server_metrics** | 性能指标监控 | 无参数 - 返回请求统计、性能指标、缓存情况 |
| **clear_cache**        | 缓存管理     | 无参数 - 清空所有缓存数据                 |

### 参数说明详解

#### 抓取方法 (method)

- **auto**: 智能选择最佳方法，基于网站特性自动判断
- **simple**: 快速 HTTP 请求，不支持 JavaScript，适合静态网页
- **scrapy**: Scrapy 框架，适合大规模数据抓取和复杂页面
- **selenium**: 浏览器渲染，支持 JavaScript 和动态内容

#### 数据提取配置 (extract_config)

```json
{
  "title": "h1",
  "content": {
    "selector": ".content p",
    "multiple": true,
    "attr": "text"
  },
  "links": {
    "selector": "a",
    "multiple": true,
    "attr": "href"
  }
}
```

#### 等待元素 (wait_for_element)

- `.content` - 类选择器
- `#main-article` - ID 选择器
- `[data-loaded]` - 属性选择器
- `button[type="submit"]` - 复合选择器

#### 表单数据 (form_data)

```json
{
  "#username": "用户名",
  "input[name=\"password\"]": "密码",
  "select[name=country]": "China",
  "input[value=male]": "click",
  "input[name=agree]": true
}
```

### 图片嵌入选项 (embed_options)

```json
{
  "max_images": 50,
  "max_bytes_per_image": 2000000,
  "timeout_seconds": 10
}
```

#### PDF 处理方法 (method)

- **auto**: 自动选择最佳提取方法
- **pymupdf**: PyMuPDF 引擎，适合复杂布局和图表
- **pypdf**: PyPDF 引擎，适合简单纯文本文档

#### 页面范围 (page_range)

- `[0, 10]` - 提取第 0-10 页（页码从 0 开始）
- `[5, -1]` - 从第 5 页到最后一页
- `null` - 提取所有页面（默认）

#### 结构化数据类型 (data_type)

- **all**: 提取所有类型数据（默认）
- **contact**: 仅提取联系方式（邮箱、电话、传真）
- **social**: 仅提取社交媒体链接和账号
- **content**: 仅提取文章内容和元数据
- **products**: 仅提取产品和价格信息
- **addresses**: 仅提取地址相关信息

### 高级功能参数

#### 格式化选项 (formatting_options)

```json
{
  "format_tables": true,
  "detect_code_language": true,
  "format_quotes": true,
  "enhance_images": true,
  "optimize_links": true,
  "format_lists": true
}
```

#### 增强 PDF 处理选项 (enhanced_options)

用于 PDF 内容深度提取的高级配置选项：

```json
{
  "output_dir": "./extracted_assets", // 输出目录路径
  "image_size": [800, 600], // 图像尺寸调整 [width, height]
  "image_format": "png", // 图像格式 (png, jpg)
  "image_quality": 90 // 图像质量 (1-100，仅适用于JPEG)
}
```

#### PDF 增强提取参数

- **extract_images**: 是否从 PDF 中提取图像并保存为本地文件 (默认: true)

  - 支持 PNG/JPG 格式输出
  - 可选择本地文件引用或 base64 嵌入
  - 自动调整图像尺寸和优化质量

- **extract_tables**: 是否从 PDF 中提取表格并转换为 Markdown 表格格式 (默认: true)

  - 智能识别各种格式的表格（管道符分隔、制表符分隔、空格分隔）
  - 自动保留表格的行列关系和内容完整性
  - 转换为标准 Markdown 表格格式

- **extract_formulas**: 是否从 PDF 中提取数学公式并保持 LaTeX 格式 (默认: true)

  - 识别多种 LaTeX 格式的数学公式
  - 支持内联公式 (`$...$` 或 `\(...\)` 格式)
  - 支持块级公式 (`$$...$$` 或 `\[...\]` 格式)

- **embed_images**: 是否将提取的图像以 base64 格式嵌入到 Markdown 文档中 (默认: false)
  - true: 图像直接嵌入文档，便于分享
  - false: 图像保存为本地文件，减少文档大小

#### 隐身抓取参数

- **scroll_page**: 滚动页面加载动态内容
- **method**: selenium(推荐) 或 playwright
- **wait_for_element**: 建议设置以提高成功率

#### 域名过滤示例

```json
{
  "filter_domains": ["example.com", "blog.example.com"],
  "exclude_domains": ["ads.com", "tracker.net"],
  "internal_only": false
}
```

### 企业级特性

- **错误处理**: 完善的错误分类和处理
- **性能监控**: 详细的请求指标和统计
- **速率限制**: 防止服务器过载
- **代理支持**: 支持 HTTP 代理配置
- **随机 UA**: 防检测的用户代理轮换
- **智能重试**: 指数退避重试机制
- **结果缓存**: 内存缓存提升性能

## 📋 项目现状

### 项目结构

```
data-extractor/
├── extractor/                          # 核心引擎模块
│   ├── __init__.py                     # 包初始化 (v0.1.4)
│   ├── server.py                       # FastMCP 服务器与 14 个 MCP 工具
│   ├── scraper.py                      # WebScraper 核心抓取引擎
│   ├── advanced_features.py            # 反检测与表单自动化
│   ├── markdown_converter.py           # Markdown 转换引擎 (8种格式化选项)
│   ├── pdf_processor.py               # PDF 处理引擎 (PyMuPDF/PyPDF2双引擎)
│   ├── config.py                       # 配置管理 (DataExtractorSettings)
│   └── utils.py                        # 企业级工具集 (限流、重试、缓存等)
├── examples/                           # 使用示例
│   ├── basic_usage.py                  # 基础用法示例
│   └── extraction_configs.py           # 数据提取配置示例
├── tests/                              # 完整测试体系 (191个测试)
│   ├── unit/                           # 单元测试 (98个测试)
│   │   ├── test_scraper.py              # WebScraper 核心引擎测试
│   │   ├── test_advanced_features.py    # 高级功能测试 (反检测、表单处理)
│   │   ├── test_utils.py                # 工具类测试 (限流、重试、缓存等)
│   │   ├── test_markdown_converter.py   # MarkdownConverter 测试
│   │   └── test_pdf_processor.py        # PDF 处理引擎测试
│   ├── integration/                     # 集成测试 (93个测试)
│   │   ├── test_mcp_tools.py            # 12个MCP工具集成测试
│   │   ├── test_comprehensive_integration.py # 综合集成测试 (端到端、性能、实际场景)
│   │   ├── test_pdf_integration.py      # PDF 工具实际执行验证 (13项)
│   │   ├── test_cross_tool_integration.py # 跨工具协作流程验证 (9项)
│   │   └── test_end_to_end_integration.py # 端到端现实场景测试 (34项)
│   └── conftest.py                      # pytest 配置和共享 fixtures
├── scripts/
│   └── setup.sh                        # 快速安装脚本
├── .claude/                            # Claude Code 配置
│   └── settings.local.json             # IDE 本地设置
├── .vscode/                            # VS Code 配置
│   └── settings.json                   # 编辑器设置
├── TESTING.md                          # 测试文档 (30KB)
├── TEST_RESULTS.md                     # 测试执行报告 (9KB)
├── CHANGELOG.md                        # 版本变更日志 (17KB)
├── CLAUDE.md                           # Claude Code 项目指导
├── .prompts.md                         # 项目里程碑和任务清单
├── .env.example                        # 环境变量配置示例
├── .mcp.json                           # MCP 服务器配置
├── .gitignore                          # Git 忽略规则
├── mypy.ini                            # 类型检查配置
├── pyproject.toml                      # 项目配置和依赖管理
└── uv.lock                             # 依赖锁定文件 (311KB)
```

### ✅ 版本里程碑

**v0.1.5 (2025/09/12)** - MCP 工具架构重构与标准化

- ✅ **MCP 工具标准化**: 全面重构 14 个 MCP 工具，统一使用 Annotated[*, Field(...)] 参数约束模式，提供清晰的参数描述和示例
- **核心重构**: 全面重构 14 个 MCP 工具，全面测试系统优化，从 BaseModel 子类实现迁移到 `Annotated[*, Field(...)]` 参数约束模式
- **参数标准化**: 统一参数定义规范，提供清晰的中文描述和示例说明
- **输出模式优化**: 增强响应模型描述，提升 MCP Client 兼容性
- **测试适配**: 全面更新测试用例，适配新的函数签名和参数传递方式
- **文档同步**: 更新 README.md 和测试文档，反映架构变更

**v0.1.6 (2025/11/19)** - PDF 增强功能与内容深度提取

- ✨ **PDF 增强处理**: 新增增强版 PDF 处理器，支持图像、表格、数学公式的深度提取
- **🖼️ 图像提取**: 从 PDF 中提取图像并保存为本地文件或 base64 嵌入，支持尺寸调整和质量优化
- **📊 表格转换**: 智能识别 PDF 表格并转换为标准 Markdown 表格格式，保持数据结构完整性
- **🧮 公式提取**: 识别并提取 LaTeX 格式的数学公式，支持内联和块级公式格式保持
- **📝 结构化输出**: 自动生成包含提取资源的结构化 Markdown 文档，提供详细的提取统计信息
- **⚙️ 高级配置**: 新增 enhanced_options 参数，支持自定义输出目录、图像格式、质量控制等高级配置
- **📈 性能优化**: 提供详细的性能对比参考和故障排除指南，支持选择性功能启用
- **🔧 向后兼容**: 保持所有现有 API 的向后兼容性，新功能默认启用但可选择性关闭

**v0.1.4 (2025/09/06)** - 基于 Scrapy + FastMCP 构建的企业级网页抓取 MCP Server

- ✅ **完整测试体系**: 219 个测试用例，通过率 98.6%+，包含单元测试和强化集成测试
- ✅ **集成测试强化**: 新增 PDF 工具实际执行验证、跨工具协作流程、端到端现实场景测试
- ✅ **代码质量优化**: 类型注解完善，从 black 迁移到 ruff 格式化
- ✅ **配置统一**: 项目名称从 scrapy-mcp 更名为 data-extractor，配置前缀统一
- ✅ **文档完善**: README、CHANGELOG、TESTING 文档体系建立
- 新增 14 个 MCP 工具的完整测试覆盖
- 增强单元测试和集成测试
- 改进测试报告和文档
- 添加性能测试和负载测试

### v0.1.3 (2025-09-06)

- **Markdown 转换功能**: 新增 2 个 MCP 工具，包含页面转 Markdown 和批量转换功能
- **高级格式化能力**: 8 种可配置格式化选项，包括表格对齐、代码语言检测、智能排版
- **完整测试体系**: 162 个测试用例 (131 个单元测试 + 31 个集成测试)，通过率 99.4%
- **综合集成测试**: 端到端功能测试、性能负载测试、错误恢复韧性测试、系统健康诊断
- **测试文档完善**: 详细的 TESTING.md (包含测试架构、执行指南、故障排除)
- **质量保障**: A+ 评级，生产就绪标准，pytest 异步测试、Mock 策略、性能基准
- 基本单元测试和集成测试
- 初始 CI 配置

### v0.1.2 (2025-09-06)

- **测试框架建设**: 建立完整的单元测试和集成测试体系，19 个基础测试全部通过
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

详细的安装、配置和使用指南请参考 **[User Guide](docs/6-User-Guide.md)**。

### 📦 快速安装

```bash
# 克隆仓库
git clone https://github.com/ThreeFish-AI/data-extractor.git
cd data-extractor

# 快速设置
./scripts/setup.sh

# 启动服务器
uv run data-extractor
```

### 🔧 MCP Client 配置

在 Claude Desktop 中配置 data-extractor MCP 服务器，详细配置说明请参考 **[User Guide - MCP Server 配置](docs/6-User-Guide.md#mcp-server-配置)**。

## 🛠️ 工具详情

### 📋 返回值规范

所有 MCP 工具都遵循 FastMCP 标准，使用强类型的 Pydantic BaseModel 定义返回值：

#### 通用字段说明

- **`success`**: `bool` - 所有工具都包含此字段，表示操作是否成功执行
- **`error`**: `str` (可选) - 失败时包含具体的错误信息
- **时间戳**: 大部分工具包含时间相关字段，如 `timestamp`、`operation_time` 等

#### 响应模型类型

| 响应类型              | 用途          | 主要字段                                        |
| --------------------- | ------------- | ----------------------------------------------- |
| `ScrapeResponse`      | 单页面抓取    | `url`, `method`, `data`, `metadata`             |
| `BatchScrapeResponse` | 批量抓取      | `total_urls`, `successful_count`, `results`     |
| `LinksResponse`       | 链接提取      | `total_links`, `links`, `internal_links_count`  |
| `MarkdownResponse`    | Markdown 转换 | `markdown_content`, `word_count`, `metadata`    |
| `PDFResponse`         | PDF 转换      | `content`, `page_count`, `word_count`           |
| `MetricsResponse`     | 性能指标      | `total_requests`, `success_rate`, `cache_stats` |

### 1. scrape_webpage

基础网页爬取工具，支持多种方法和自定义提取规则。

**参数:**

- `url`: 要爬取的 URL
- `method`: 爬取方法 (auto/simple/scrapy/selenium)
- `extract_config`: 数据提取配置 (可选)
- `wait_for_element`: 等待的 CSS 选择器 (Selenium 专用)

**返回值类型:** `ScrapeResponse`

| 字段名      | 类型             | 描述               |
| ----------- | ---------------- | ------------------ |
| `success`   | `bool`           | 操作是否成功       |
| `url`       | `str`            | 被抓取的 URL       |
| `method`    | `str`            | 使用的抓取方法     |
| `data`      | `Dict[str, Any]` | 抓取到的数据       |
| `metadata`  | `Dict[str, Any]` | 页面元数据         |
| `error`     | `str`            | 错误信息（如果有） |
| `timestamp` | `datetime`       | 抓取时间戳         |

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

**返回值示例:**

```json
{
  "success": true,
  "url": "https://example.com",
  "method": "auto",
  "data": {
    "title": "网站标题",
    "content": ["段落1内容", "段落2内容"]
  },
  "metadata": {
    "title": "网站标题",
    "description": "网站描述"
  },
  "timestamp": "2025-09-17T13:45:00"
}
```

### 2. scrape_multiple_webpages

并发爬取多个网页。

**返回值类型:** `BatchScrapeResponse`

| 字段名             | 类型                   | 描述                |
| ------------------ | ---------------------- | ------------------- |
| `success`          | `bool`                 | 整体操作是否成功    |
| `total_urls`       | `int`                  | 总 URL 数量         |
| `successful_count` | `int`                  | 成功抓取的数量      |
| `failed_count`     | `int`                  | 失败的数量          |
| `results`          | `List[ScrapeResponse]` | 每个 URL 的抓取结果 |
| `summary`          | `Dict[str, Any]`       | 批量操作摘要信息    |

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

**返回值类型:** `LinksResponse`

| 字段名                 | 类型             | 描述               |
| ---------------------- | ---------------- | ------------------ |
| `success`              | `bool`           | 操作是否成功       |
| `url`                  | `str`            | 源页面 URL         |
| `total_links`          | `int`            | 总链接数量         |
| `links`                | `List[LinkItem]` | 提取的链接列表     |
| `internal_links_count` | `int`            | 内部链接数量       |
| `external_links_count` | `int`            | 外部链接数量       |
| `error`                | `str`            | 错误信息（如果有） |

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

**返回值类型:** `MetricsResponse`

| 字段名                  | 类型             | 描述               |
| ----------------------- | ---------------- | ------------------ |
| `success`               | `bool`           | 操作是否成功       |
| `total_requests`        | `int`            | 总请求数           |
| `successful_requests`   | `int`            | 成功请求数         |
| `failed_requests`       | `int`            | 失败请求数         |
| `success_rate`          | `float`          | 成功率             |
| `average_response_time` | `float`          | 平均响应时间（秒） |
| `uptime_seconds`        | `float`          | 运行时间（秒）     |
| `cache_stats`           | `Dict[str, Any]` | 缓存统计           |

### 10. clear_cache

清除缓存的爬取结果。

**返回值类型:** `CacheOperationResponse`

| 字段名              | 类型    | 描述             |
| ------------------- | ------- | ---------------- |
| `success`           | `bool`  | 操作是否成功     |
| `cleared_items`     | `int`   | 清理的缓存项数量 |
| `cache_size_before` | `int`   | 清理前缓存大小   |
| `cache_size_after`  | `int`   | 清理后缓存大小   |
| `operation_time`    | `float` | 操作耗时（秒）   |
| `message`           | `str`   | 操作结果消息     |

### 11. convert_webpage_to_markdown

将网页内容抓取并转换为 Markdown 格式，适用于文档处理、内容分析和存储。

**参数:**

- `url`: 要抓取和转换的 URL
- `method`: 抓取方法 (auto/simple/scrapy/selenium，默认 auto)
- `extract_main_content`: 是否仅提取主要内容区域 (默认 true)
- `include_metadata`: 是否包含页面元数据 (默认 true)
- `custom_options`: 自定义 Markdown 转换选项 (可选)
- `wait_for_element`: 等待的 CSS 选择器 (Selenium 专用)
- `formatting_options`: 高级格式化选项，包含以下配置:
  - `format_tables`: 表格对齐格式化 (默认 true)
  - `detect_code_language`: 自动检测代码语言 (默认 true)
  - `format_quotes`: 引用块格式化 (默认 true)
  - `enhance_images`: 图片描述增强 (默认 true)
  - `optimize_links`: 链接格式优化 (默认 true)
  - `format_lists`: 列表格式化 (默认 true)
  - `format_headings`: 标题格式化和间距 (默认 true)
  - `apply_typography`: 排版优化 (智能引号、破折号等，默认 true)
  - 新增图片嵌入选项:
    - `embed_images` (boolean): 是否将页面中的图片以 data URI 形式嵌入 Markdown (默认 false)
    - `embed_options` (object): 图片嵌入行为配置
      - `max_images` (int): 最大嵌入图片数量 (默认 50)
      - `max_bytes_per_image` (int): 单张图片最大字节数上限，超过则保留原链接 (默认 2,000,000)
      - `timeout_seconds` (int): 下载图片的超时时间 (默认 10)

**功能特性:**

- **智能内容提取**: 自动识别并提取网页主要内容区域
- **清理处理**: 移除广告、导航栏、侧边栏等无关内容
- **URL 转换**: 将相对 URL 转换为绝对 URL
- **格式优化**: 清理多余空白行，优化 Markdown 格式
- **元数据丰富**: 包含标题、描述、字数统计等信息
- **高级格式化**: 提供 8 种可配置的格式化选项
  - 表格自动对齐和格式化
  - 代码块语言自动检测 (支持 Python、JavaScript、HTML、SQL 等)
  - 引用块格式优化
  - 图片描述自动生成和增强
  - 链接格式优化和去重
  - 列表格式统一化
  - 标题层级和间距优化
  - 排版增强 (智能引号、em 破折号、空格清理)

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
  },
  "formatting_options": {
    "format_tables": true,
    "detect_code_language": true,
    "enhance_images": true,
    "apply_typography": false
  },
  "embed_images": true,
  "embed_options": {
    "max_images": 10,
    "max_bytes_per_image": 1500000,
    "timeout_seconds": 8
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
- `formatting_options`: 高级格式化选项 (与单页转换相同配置)
- `embed_images` / `embed_options`: 与单页相同，用于批量图片嵌入

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

### 13. convert_pdf_to_markdown

将 PDF 文档转换为 Markdown 格式，支持 URL 和本地文件路径，适用于文档处理、内容分析和知识管理。

**参数:**

- `pdf_source`: PDF URL 或本地文件路径
- `method`: 提取方法 (auto/pymupdf/pypdf2，默认 auto)
- `include_metadata`: 是否包含 PDF 元数据 (默认 true)
- `page_range`: 页面范围 [start, end] 用于部分提取 (可选)
- `output_format`: 输出格式 (markdown/text，默认 markdown)
- `extract_images`: 是否从 PDF 中提取图像并保存为本地文件 (默认 true)
- `extract_tables`: 是否从 PDF 中提取表格并转换为 Markdown 表格格式 (默认 true)
- `extract_formulas`: 是否从 PDF 中提取数学公式并保持 LaTeX 格式 (默认 true)
- `embed_images`: 是否将提取的图像以 base64 格式嵌入到 Markdown 文档中 (默认 false)
- `enhanced_options`: 增强处理选项 (可选)

**enhanced_options 详细配置:**

```json
{
  "output_dir": "./extracted_assets", // 输出目录路径
  "image_size": [800, 600], // 图像尺寸调整 [width, height]
  "image_format": "png", // 图像格式 (png, jpg)
  "image_quality": 90 // 图像质量 (1-100，仅适用于JPEG)
}
```

**功能特性:**

#### 🆕 增强内容提取功能

- **🖼️ 图像提取**: 从 PDF 页面中提取所有图像元素，支持本地存储和 Markdown 集成
- **📊 表格提取**: 智能识别各种格式的表格，转换为标准 Markdown 表格格式
- **🧮 数学公式提取**: 识别多种 LaTeX 格式的数学公式，保持原始 LaTeX 格式

#### 标准功能

- **多源支持**: 支持 PDF URL 和本地文件路径
- **多引擎支持**: PyMuPDF (fitz) 和 PyPDF2 双引擎自动选择
- **部分提取**: 支持指定页面范围的部分提取
- **元数据提取**: 包含标题、作者、创建日期等完整元数据
- **智能转换**: 自动检测标题层级和格式化
- **错误恢复**: 引擎失败时自动切换备用方法

#### 生成的 Markdown 结构示例

```markdown
# 原始文档内容

...

## Extracted Images

![图表 1](img_0_0_001.png)

_Dimensions: 800×600px_
_Source: Page 1_

## Extracted Tables

**数据统计表**

| 项目   | 数值   | 单位 |
| ------ | ------ | ---- |
| 销售额 | 125000 | 元   |

_Table: 3 rows × 3 columns_
_Source: Page 2_

## Mathematical Formulas

爱因斯坦质能方程：$E = mc^2$

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

_Source: Page 3_
```

**基础示例:**

```json
{
  "pdf_source": "https://example.com/document.pdf",
  "method": "auto",
  "include_metadata": true,
  "page_range": [0, 10],
  "output_format": "markdown"
}
```

**启用所有增强功能:**

```json
{
  "pdf_source": "https://example.com/document.pdf",
  "method": "pymupdf",
  "output_format": "markdown",
  "extract_images": true,
  "extract_tables": true,
  "extract_formulas": true,
  "embed_images": false,
  "enhanced_options": {
    "output_dir": "./extracted_assets",
    "image_size": [800, 600]
  }
}
```

**返回示例 (包含增强资源):**

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
    "source": "https://example.com/document.pdf",
    "method_used": "pymupdf",
    "word_count": 2500,
    "character_count": 15000,
    "enhanced_assets": {
      "images": {
        "count": 3,
        "files": ["img_0_0_001.png", "img_1_0_002.png"],
        "total_size_mb": 2.4
      },
      "tables": {
        "count": 2,
        "total_rows": 8,
        "total_columns": 6
      },
      "formulas": {
        "count": 5,
        "inline_count": 3,
        "block_count": 2
      },
      "output_directory": "/path/to/extracted_assets"
    }
  }
}
```

#### 使用场景示例

**学术论文处理:**

```json
{
  "pdf_source": "research_paper.pdf",
  "extract_formulas": true,
  "extract_images": true,
  "extract_tables": true
}
```

**技术文档转换:**

```json
{
  "pdf_source": "technical_manual.pdf",
  "extract_images": true,
  "extract_tables": true,
  "embed_images": true,
  "enhanced_options": {
    "image_size": [1200, 900]
  }
}
```

**性能注意事项:**

- 启用所有增强功能会增加处理时间，特别是图像提取 (+30-50%)
- 提取的图像会占用本地存储空间
- 处理大型 PDF 文件时注意内存使用情况

### 14. batch_convert_pdfs_to_markdown

批量转换多个 PDF 文档为 Markdown 格式，支持并发处理提升效率，适用于大规模文档处理。

**参数:**

- `pdf_sources`: PDF URL 或本地文件路径列表
- `method`: 提取方法 (auto/pymupdf/pypdf2，默认 auto)
- `include_metadata`: 是否包含 PDF 元数据 (默认 true)
- `page_range`: 页面范围 [start, end] 应用于所有 PDF (可选)
- `output_format`: 输出格式 (markdown/text，默认 markdown)

**功能特性:**

- **并发处理**: 同时处理多个 PDF 文档提升效率
- **一致配置**: 所有 PDF 使用相同的转换设置
- **详细统计**: 提供成功/失败统计和汇总信息
- **错误容错**: 单个 PDF 失败不影响其他文档处理
- **批量优化**: 针对大量文档优化的内存和性能配置

**示例:**

```json
{
  "pdf_sources": [
    "https://example.com/doc1.pdf",
    "/local/path/doc2.pdf",
    "https://example.com/doc3.pdf"
  ],
  "method": "auto",
  "include_metadata": true,
  "output_format": "markdown"
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
        "source": "https://example.com/doc1.pdf",
        "text": "原始文本内容",
        "markdown": "# 文档1标题\n\n内容...",
        "metadata": {...},
        "word_count": 1500
      },
      {
        "success": true,
        "source": "/local/path/doc2.pdf",
        "text": "原始文本内容",
        "markdown": "# 文档2标题\n\n内容...",
        "metadata": {...},
        "word_count": 2000
      }
    ],
    "summary": {
      "total_pdfs": 3,
      "successful": 2,
      "failed": 1,
      "total_pages_processed": 45,
      "total_words_extracted": 3500,
      "method_used": "auto",
      "output_format": "markdown"
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

## 📋 详细的架构设计和使用指南

详细的架构设计、API 接口、开发流程和高级使用场景请参考 **[User Guide](docs/6-User-Guide.md)**：

- **[架构设计](docs/6-User-Guide.md#架构设计)** - 核心引擎层和 MCP 工具集详解
- **[API 编程接口](docs/6-User-Guide.md#api-编程接口)** - 直接 Python 调用示例
- **[开发与发布](docs/6-User-Guide.md#开发与发布)** - CI/CD 流程和版本管理
- **[高级使用场景](docs/6-User-Guide.md#高级使用场景)** - 电商、新闻、学术论文等实际应用案例

## 📋 版本信息

详细的版本管理和发布流程请参考 **[User Guide - 开发与发布](docs/6-User-Guide.md#开发与发布)**。

### 当前版本

- **最新稳定版本**: v0.1.6
- **Python 要求**: 3.12+
- **发布状态**: [![Release](https://github.com/ThreeFish-AI/data-extractor/actions/workflows/release.yml/badge.svg)](https://github.com/ThreeFish-AI/data-extractor/actions/workflows/release.yml)

## 🎯 快速参考

### 核心特性概览

- **14 个专业 MCP 工具**：网页抓取、PDF 处理、Markdown 转换、表单自动化
- **智能方法选择**：auto/simple/scrapy/selenium/stealth 多种抓取策略
- **企业级特性**：速率限制、缓存、重试、监控、代理支持
- **增强 PDF 处理**：图像、表格、数学公式深度提取

### 工具选择指南

| 网站类型        | 推荐方法 | 用途                 |
| --------------- | -------- | -------------------- |
| 静态网页        | simple   | 快速抓取，资源消耗低 |
| JavaScript 网站 | selenium | 动态内容渲染         |
| 大规模抓取      | scrapy   | 并发处理，管道化     |
| 有反爬保护      | stealth  | 隐身抓取，避免检测   |

## 🔍 故障排除与支持

详细的故障排除、性能优化和最佳实践请参考 **[User Guide](docs/6-User-Guide.md)**：

- **[故障排除](docs/6-User-Guide.md#故障排除)** - 常见问题和解决方案
- **[性能优化](docs/6-User-Guide.md#性能优化)** - 内存、网络、缓存优化策略
- **[最佳实践](docs/6-User-Guide.md#最佳实践)** - 方法选择、合规使用、监控维护

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📞 支持

- **GitHub Issues**: [提交问题](https://github.com/ThreeFish-AI/data-extractor/issues)
- **详细文档**: [User Guide](docs/6-User-Guide.md)
- **测试文档**: [TESTING.md](TESTING.md)
- **变更日志**: [CHANGELOG.md](CHANGELOG.md)

---

**注意**: 请负责任地使用此工具，遵守网站的使用条款和 robots.txt 规则，尊重网站的知识产权。
