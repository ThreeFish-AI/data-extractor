---
id: data-extractor
sidebar_position: 1
title: Data Extractor
description: Readme of Data Extractor
last_update:
  author: Aurelius
  date: 2025-11-24
tags:
  - README
  - Data Extractor
---

Data Extractor 是一个基于 FastMCP 和 Scrapy、markdownify、pypdf、pymupdf 联合构建的强大、稳定的网页内容、PDF 内容提取 MCP Server，具备转换 Web Page、PDF Document 为 Markdown 的能力，专为商业环境中的长期使用而设计。

## 🛠️ MCP Server 核心工具 (14 个)

### Web Page

| 工具名称                               | 功能描述           | 主要参数                                                                                            |
| -------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| **scrape_webpage**                     | 单页面抓取         | `url`, `method`(自动选择), `extract_config`(选择器配置), `wait_for_element`(CSS 选择器)             |
| **scrape_multiple_webpages**           | 批量页面抓取       | `urls`(列表), `method`(统一方法), `extract_config`(全局配置)                                        |
| **scrape_with_stealth**                | 反检测抓取         | `url`, `method`(selenium/playwright), `scroll_page`(滚动加载), `wait_for_element`                   |
| **fill_and_submit_form**               | 表单自动化         | `url`, `form_data`(选择器:值), `submit`(是否提交), `submit_button_selector`                         |
| **extract_links**                      | 专业链接提取       | `url`, `filter_domains`(域名过滤), `exclude_domains`(排除域名), `internal_only`(仅内部)             |
| **extract_structured_data**            | 结构化数据提取     | `url`, `data_type`(all/contact/social/content/products/addresses)                                   |
| **get_page_info**                      | 页面信息获取       | `url`(目标 URL) - 返回标题、状态码、元数据                                                          |
| **check_robots_txt**                   | 爬虫规则检查       | `url`(域名 URL) - 检查 robots.txt 规则                                                              |
| **convert_webpage_to_markdown**        | 页面转 Markdown    | `url`, `method`, `extract_main_content`(提取主内容), `embed_images`(嵌入图片), `formatting_options` |
| **batch_convert_webpages_to_markdown** | 批量 Markdown 转换 | `urls`(列表), `method`, `extract_main_content`, `embed_images`, `embed_options`                     |

### PDF Document

| 工具名称                           | 功能描述        | 主要参数                                                                            |
| ---------------------------------- | --------------- | ----------------------------------------------------------------------------------- |
| **convert_pdf_to_markdown**        | PDF 转 Markdown | `pdf_source`(URL/路径), `method`(auto/pymupdf/pypdf), `page_range`, `output_format` |
| **batch_convert_pdfs_to_markdown** | 批量 PDF 转换   | `pdf_sources`(列表), `method`, `page_range`, `output_format`, `include_metadata`    |

### 服务管理

| 工具名称               | 功能描述     | 主要参数                                  |
| ---------------------- | ------------ | ----------------------------------------- |
| **get_server_metrics** | 性能指标监控 | 无参数 - 返回请求统计、性能指标、缓存情况 |
| **clear_cache**        | 缓存管理     | 无参数 - 清空所有缓存数据                 |

## 🎯 快速参考

- [用户指南](docs/6-User-Guide.md)
- [架构设计](docs/1-Framework.md)
- [开发指南](docs/2-Development.md)
- [测试指南](docs/3-Testing.md)
- [配置系统](docs/4-Configuration.md)
- [常用指令](docs/5-Commands.md)
- [版本里程](CHANGELOG.md)

## 🤝 贡献

欢迎提交 [Issue](https://github.com/ThreeFish-AI/data-extractor/issues) 和 [Pull Request](https://github.com/ThreeFish-AI/data-extractor/pulls) 来改进这个项目。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**注意**: 请负责任地使用此工具，遵守网站的使用条款和 robots.txt 规则，尊重网站的知识产权。
