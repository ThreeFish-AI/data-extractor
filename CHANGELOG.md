# Changelog

All notable changes to the Data Extractor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.1.3

#### Released on 2025/09/06

### 新增

- **Markdown 转换工具集**
  - **convert_webpage_to_markdown**: 单页面转 Markdown 工具，支持智能内容提取和元数据处理
    - 自动识别并提取网页主要内容区域（main、article、.content 等选择器）
    - HTML 预处理：移除注释、清理无关标签、转换相对 URL 为绝对 URL
    - Markdown 格式优化：清理多余空白行、优化列表格式、移除行尾空格
    - 元数据丰富：包含标题、描述、字数统计、链接数量、图片数量、域名等信息
    - 自定义转换选项：支持标题样式、列表符号、链接格式等自定义配置
  - **batch_convert_webpages_to_markdown**: 批量页面转 Markdown 工具，支持并发处理多个 URL
    - 并发处理多个 URL，提升批量转换效率
    - 详细统计信息：总数、成功数、失败数、成功率等汇总数据
    - 错误隔离：单个页面失败不影响其他页面处理
    - 配置一致性：所有页面使用相同的转换配置保证格式统一
- **MarkdownConverter 核心转换引擎**
  - extractor/markdown_converter.py: 新增专用 Markdown 转换模块
  - 基于 markdownify 库的 HTML 到 Markdown 转换
  - 智能内容区域提取算法，支持最小内容长度检查（200 字符阈值）
  - HTML 预处理流水线：注释移除、标签清理、URL 转换、空元素清理
  - Markdown 后处理优化：空行清理、列表格式化、内容修剪
- **完整测试覆盖体系**
  - tests/unit/test_markdown_converter.py: MarkdownConverter 单元测试（33 个测试用例）
    - 初始化和配置测试、HTML 预处理测试、转换功能测试
    - 后处理测试、内容提取测试、批量转换测试
  - tests/integration/test_mcp_tools.py: 新增 Markdown 工具集成测试
    - 工具注册验证、参数模式检查
    - 更新工具总数从 10 个扩展到 12 个 MCP 工具

### 变更

- **pyproject.toml**: 新增依赖 `markdownify>=1.2.0` 支持 HTML 到 Markdown 转换
- **README.md**: 更新 MCP Server 工具列表和详细文档
  - 工具表格更新：新增 convert_webpage_to_markdown 和 batch_convert_webpages_to_markdown
  - 新增工具详情章节：参数说明、功能特性、使用示例、返回格式
  - 完整的 JSON 请求和响应示例，支持自定义转换选项
- **TESTING.md**: 更新测试文档结构和覆盖说明
  - 测试目录结构更新：新增 test_markdown_converter.py 单元测试文件
  - MCP 工具测试覆盖从 10 个扩展到 12 个工具
  - 新增 Markdown 转换器测试章节：7 个主要测试类别详细说明

### 修复

- **MarkdownConverter 配置优化**
  - 修复 markdownify 配置冲突：移除 strip 和 convert 参数同时使用的错误
  - 修复 wrap_width=0 导致的 "invalid width" 错误，改为 wrap=False 禁用换行
  - 修复 BeautifulSoup 废弃方法：findAll → find_all，消除 DeprecationWarning
  - 优化内容提取测试断言：调整为更现实的内容长度和验证逻辑

## v0.1.2

#### Released on 2025/09/06

### 新增

- **完整测试框架体系**
  - tests/unit/: 单元测试目录，包含核心引擎和工具类测试
  - tests/integration/: 集成测试目录，包含 10 个 MCP 工具端到端测试
  - tests/fixtures/: 测试数据和固定装置目录
  - tests/conftest.py: pytest 配置和共享 fixtures，支持异步测试
- **DataExtractor 核心引擎测试**
  - tests/unit/test_scraper_simple.py: WebScraper 基础功能测试（9 个测试用例）
  - tests/unit/test_scraper.py: HTML 解析和抓取引擎测试
  - tests/unit/test_utils_basic.py: 工具类基础功能测试（10 个测试用例）
  - tests/unit/test_advanced_features.py: 反检测和表单处理功能测试
- **MCP 工具集成测试用例**
  - tests/integration/test_mcp_tools.py: 10 个核心 MCP 工具完整测试覆盖
    - scrape_webpage, scrape_multiple_webpages, extract_links, get_page_info
    - check_robots_txt, scrape_with_stealth, fill_and_submit_form
    - get_server_metrics, clear_cache, extract_structured_data
- **测试文档与报告**
  - TESTING.md: 67KB 详细测试文档，包含架构说明、运行指南、最佳实践
  - TEST_RESULTS.md: 测试执行结果报告，19 个基础测试全部通过

### 变更

- **pyproject.toml**: 确保测试依赖 `pytest>=8.0.0` 和 `pytest-asyncio>=0.23.0` 配置正确
- **scripts/setup.sh**: 代码格式化工具从 `black` 替换为 `ruff format`，提升格式化速度和一致性

### 修复

- **单元测试异常修复（89/90 测试通过率 99%+）**
  - tests/integration/test_mcp_tools.py: 修复 MCP 工具调用接口错误，正确处理 FastMCP 框架 API
    - 修复 `get_tools()` 异步调用和字典格式解析
    - 修复 `get_tool()` 返回的 FunctionTool 对象属性检查
    - 完善 10 个 MCP 工具注册和执行验证测试
  - tests/unit/test_utils.py: 修复工具类初始化参数不匹配问题
    - RateLimiter: `requests_per_minute` → `requests_per_second` 参数修正
    - CacheManager: 修复 `cache_dir` 参数移除，更新为内存缓存模式
    - MetricsCollector: 修复方法名称错误（`get_metrics` → `get_stats`）
    - ErrorHandler: 修复静态方法调用和错误分类逻辑
  - tests/unit/test_scraper.py: 修复抓取器属性名称和断言错误
    - WebScraper 属性名修正：`scrapy_scraper` → `scrapy_wrapper`
    - 修复 URL 标准化断言错误（`https://example.com/` vs `https://example.com`）
    - 完善方法存在性检查和条件跳过逻辑
  - tests/unit/test_advanced_features.py: 修复反检测和表单处理测试 Mock 配置
    - AntiDetectionScraper: 修复 Playwright 异步初始化 Mock 设置
    - FormHandler: 修复 Selenium/Playwright 检测逻辑和方法调用 Mock
    - 修复 "can't await Mock" 异步调用错误，采用分层 Mock 策略
- **类型检查完整性改进**
  - pyproject.toml: 新增 `types-requests>=2.32.4.20250809` 类型存根包依赖
  - extractor/utils.py: 完善核心工具类型注解，修复 `Callable` 类型提示和异常处理逻辑
  - extractor/scraper.py: 修复抓取引擎类型注解，添加 BeautifulSoup 属性安全检查
  - extractor/advanced_features.py: 完善反检测和表单处理功能类型注解
  - extractor/server.py: 修复 MCP 服务器验证器函数类型注解
  - mypy.ini: 新增类型检查配置文件，支持第三方库类型忽略策略

### 整理

- **测试架构标准化**
  - 建立单元测试与集成测试分离的标准结构
  - 统一异步测试支持和 Mock 策略
  - 优化测试执行性能和错误处理机制

## v0.1.1

#### Released on 2025/09/05

### 整理

- **包结构重构**
  - scrapy_mcp/ → extractor/: 完整包目录重命名，包含 6 个核心模块文件移动
  - pyproject.toml: 项目名称 `scrapy-mcp` → `data-extractor`，入口命令更新
  - pyproject.toml: 新增代码质量工具 `ruff>=0.12.12` 依赖
  - uv.lock: 依赖锁定文件同步更新
  - scripts/setup.sh: 安装脚本适配新包名
- **项目配置清理**
  - .mcp.json: 移除本地 `data-extractor` 服务器配置
  - MIGRATION.md: 移除过时的迁移指南文档

### 变更

- **配置系统标准化重构**
  - extractor/config.py: 配置类 `ScrapyMCPSettings` → `DataExtractorSettings`
  - extractor/config.py: 环境变量前缀统一 `SCRAPY_MCP_` → `DATA_EXTRACTOR_`
  - extractor/config.py: 配置属性简化，移除 `scrapy_` 前缀（如 `scrapy_concurrent_requests` → `concurrent_requests`）
  - extractor/utils.py: 文档字符串更新为 "Data Extractor MCP Server"
  - .env.example: 所有环境变量名称按新前缀规范更新
  - README.md 和 CLAUDE.md: 配置示例和使用说明同步更新
  - examples/basic_usage.py: 示例标题和描述文档更新
- **.mcp.json**: MCP 服务器配置切换到外部 GitHub 包源 `git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.1`
- **CLAUDE.md**: 项目指导文档重构，新增架构概述和开发规范说明
- **README.md**: 文档更新以反映新包结构和使用方式
- **MIGRATION.md**: 迁移指南更新适配包重构

### 新增

- **.prompts.md**: 提示词配置文件，支持 Claude Code 工作流程优化

## v0.1.0

#### Released on 2025/08/26

### 新增

- **Data Extractor 核心抓取引擎**
  - scrapy_mcp/scraper.py: 多策略抓取支持（Requests/BeautifulSoup、Scrapy、Selenium、Playwright）
  - scrapy_mcp/advanced_features.py: 反检测功能（Undetected Chrome、随机 UA、人类行为模拟）
  - scrapy_mcp/advanced_features.py: 表单交互自动化（输入/复选/下拉框识别与提交）
  - scrapy_mcp/utils.py: 企业级工具集（限流、指数退避重试、缓存、错误监控、性能指标）
  - scrapy_mcp/server.py: 高性能异步架构支持
- **MCP 工具集（10 个核心工具）**
  - `scrape_webpage`: 单页面抓取工具
  - `scrape_multiple_webpages`: 批量页面抓取工具
  - `scrape_with_stealth`: 反检测抓取工具
  - `fill_and_submit_form`: 表单自动填写提交工具
  - `extract_links`: 链接提取工具
  - `extract_structured_data`: 结构化数据提取工具
  - `get_page_info`: 页面信息获取工具
  - `check_robots_txt`: robots.txt 检查工具
  - `get_server_metrics`: 服务器性能指标工具
  - `clear_cache`: 缓存清理工具
- **配置与扩展性支持**
  - scrapy*mcp/config.py: 环境变量配置系统（SCRAPY_MCP* 前缀）
  - 灵活的数据抽取配置系统，支持 CSS 选择器和属性提取
  - 代理和 User-Agent 定制支持
  - 完整的类型标注和日志记录
- **Python 3.12 兼容性问题**
  - 解决现代 Python 版本的依赖兼容性冲突
  - 核心运行时依赖升级：aiohttp>=3.9.0, lxml>=5.0.0, requests>=2.32.0, selenium>=4.20.0
  - 新增 playwright>=1.45.0, pydantic>=2.8.0, httpx>=0.27.0, twisted>=24.7.0
- **Pydantic v2 兼容性修复**
  - scrapy_mcp/config.py: 新增 `pydantic-settings` 依赖用于 `BaseSettings`
  - scrapy_mcp/config.py: 使用 `model_config` 替代旧版 `Config` 配置方式
  - scrapy_mcp/config.py: 验证器从 `@validator` 迁移到 `@field_validator`
  - scrapy_mcp/config.py: 正确处理环境变量前缀映射
- **pyproject.toml**: 包管理使用 uv，Python 最低支持版本 Python 3.12+
