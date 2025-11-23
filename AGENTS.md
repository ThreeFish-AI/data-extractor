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

本文档通过对 Data Extractor 的整体介绍（包括架构设计、功能特性、应用场景与使用指引），为 Vibe Coding Agents（如 Claude Code、Gemini Cli、CodeX、Cursor 等）提供 Data Extractor 项目的详细开发与维护总则。

## 项目概述

Data Extractor 是一个基于 FastMCP 搭建的网页与 PDF 文档内容提取与转换 Markdown 文档的 MCP Server。它基于 Scrapy 构建具备反检测能力的综合网络抓取能力，基于 markitdown、pypdf、pymupdf 等搭建 PDF 文档内容处理能力，形成专为企业级网页、PDF 内容抓取与 Markdown 转化的一套完整工具。Data Extractor 具备 14 个 MCP 工具，适用于各种 WebPage、PDF 文档内容抓取场景。

## 开发总则

- 最小充分性：充分获取和理解相关信息，如非显式说明，仅修改或增加必需内容；
- 语义连续性：保持篇幅整体意义连贯与自洽；
- 对内容的维护需要先阅读并深入理解内容，而不是通过字符的模式匹配方式进行机械操作；
- 保障代码健壮：维护完整的单元测试用例集、自动化的测试流程、说明书，通过自动化测试流程检查并修复工程模块的正确与健壮；
- 保障代码质量：从本文「开发命令」部分找到正确的指令，对代码执行质量检查、修复、格式化，障代码质量；

## 常用导航

- [架构设计](docs/Framework.md)
- [常用指令](docs/Commands.md)
- [配置系统](docs/Configuration.md)

## MCP 工具集

Data Extractor 提供了 14 个专业的 MCP 工具，按功能分为四大类别：

| 类别                   | 工具名称                           | 功能描述                    |
| ---------------------- | ---------------------------------- | --------------------------- |
| **网页抓取工具**       | scrape_webpage                     | 单页面抓取                  |
|                        | scrape_multiple_webpages           | 批量页面抓取                |
|                        | scrape_with_stealth                | 反检测抓取                  |
|                        | fill_and_submit_form               | 表单自动化                  |
| **链接和数据提取工具** | extract_links                      | 专业链接提取                |
|                        | extract_structured_data            | 结构化数据提取              |
|                        | get_page_info                      | 页面信息获取                |
|                        | check_robots_txt                   | 爬虫规则检查                |
| **Markdown 转换工具**  | convert_webpage_to_markdown        | 页面转 Markdown             |
|                        | batch_convert_webpages_to_markdown | 批量页面转 Markdown         |
|                        | convert_pdf_to_markdown            | PDF 转 Markdown（增强功能） |
|                        | batch_convert_pdfs_to_markdown     | 批量 PDF 转 Markdown        |
| **服务管理工具**       | get_server_metrics                 | 性能指标监控                |
|                        | clear_cache                        | 缓存管理                    |

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
