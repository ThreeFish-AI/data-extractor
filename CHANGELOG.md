# Changelog

All notable changes to the Data Extractor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **.mcp.json**: MCP 服务器配置切换到外部 GitHub 包源 `git+https://github.com/ThreeFish-AI/data-extractor.git@v0.1.0`
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
