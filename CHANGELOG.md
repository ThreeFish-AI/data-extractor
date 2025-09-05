# Changelog

All notable changes to the Scrapy MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 基于 Scrapy + FastMCP 构建 WebFetch MCP Server

- [x] 初始化 scrapy-mcp: 我需要一个可用于爬取网页内容的 MCP Server, 需要简单好用,页面读取能力稳定,请参考成熟技术方案,基于 Scrapy + FastMCP 帮我搭建一个这样的 MCP Server,以满足我在商业工具中长期的需求.
- [x] git init:
- [x] 帮我新增 .gitignore: 帮我增加一个 .gitignore，尽量精简并符合当前项目要求
- [x] claude code: /init
- [x] use uv: 将项目的包管理工具更换为 uv
- [x] 在 README.md 的 MCP Client 配置指引中帮我添加通过 Repo 方式和 uv 指令启动该 MCP Server 的指引
- [x] 根据项目名称、结构、GitHub Repo 地址等(git@github.com:ThreeFish-AI/scrapy-mcp.git)信息，修正 README.md 中类似 <repository-url> 的占位符、模块名、服务名、路径等
- [x] 将 Python 版本的最低要求改为 3.12，注意相关依赖的可用性。
- [x] 解决 uv run scrapy-mcp 启动异常问题；

## v0.1.1

#### Released on 2025/xx/xx

[New features and improvements]

[Bug fixes]

[Documentation, Tests and Build]

- 新增 `Github Repo@Tag` 的 MCP Client 配置方式；

[Dependency Upgrades]

## v0.1.0

#### Released on 2025/08/26

[New features and improvements]

- 初始发布：Scrapy MCP Server 核心能力与工具集
  - 多种抓取方式：Requests/BeautifulSoup、Scrapy、Selenium、Playwright
  - 反检测能力：Undetected Chrome、随机 UA、人类行为模拟、隐身抓取
  - 表单交互：自动识别输入/复选/下拉，支持提交
  - 企业级能力：限流、指数退避重试、缓存、错误分类与监控、性能指标
  - 并发处理与高性能异步架构
- MCP 工具：
  - `scrape_webpage`、`scrape_multiple_webpages`、`scrape_with_stealth`、`fill_and_submit_form`
  - `extract_links`、`extract_structured_data`、`get_page_info`、`check_robots_txt`
  - `get_server_metrics`、`clear_cache`
- 配置与可扩展性：
  - 环境变量与前缀支持、灵活的抽取配置、代理与 UA 定制
  - 模块化设计、完整日志、类型标注，易于扩展与调试
- 改进：
  - 迁移包管理到 uv；增强 `pyproject.toml` 的 uv 配置

[Bug fixes]

- 解决现代 Python 版本的依赖兼容性问题
- Pydantic v2 兼容性修复：
  - 新增 `pydantic-settings` 依赖用于 `BaseSettings`
  - 使用 `model_config` 替代 `Config` 配置方式
  - 从 `@validator` 迁移到 `@field_validator`
  - 正确处理环境变量前缀

[Documentation, Tests and Build]

- 更新安装与开发命令以使用 uv，新增 Python 版本校验脚本
- 将 Black/MyPy 等工具配置目标更新为 Python 3.12
- 完善 README、示例与高级抽取配置文档
- 依赖清单（核心运行时）：
  - aiohttp>=3.9.0, lxml>=5.0.0, requests>=2.32.0, selenium>=4.20.0
  - playwright>=1.45.0, pydantic>=2.8.0, httpx>=0.27.0, twisted>=24.7.0
- 开发与质量工具：pytest>=8.0.0, black>=24.0.0, mypy>=1.10.0

[Dependency Upgrades]

- 最低 Python 版本提升至 3.12+
- 升级运行时依赖以兼容 Python 3.12（见上）
- 升级开发依赖：pytest、black、mypy
- 包管理迁移至 uv，提升安装与解析性能
