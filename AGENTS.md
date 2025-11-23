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

- [架构设计](docs/1-Framework.md)
- [开发指南](docs/2-Development.md)
- [测试指南](docs/3-Testing.md)
- [配置系统](docs/4-Configuration.md)
- [常用指令](docs/5-Commands.md)
- [用户指南](docs/6-User-Guide.md)

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

### 企业级特性

- **错误处理**: 完善的错误分类和处理
- **性能监控**: 详细的请求指标和统计
- **速率限制**: 防止服务器过载
- **代理支持**: 支持 HTTP 代理配置
- **随机 UA**: 防检测的用户代理轮换
- **智能重试**: 指数退避重试机制
- **结果缓存**: 内存缓存提升性能
