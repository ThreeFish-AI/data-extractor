---
id: data-extractor
sidebar_position: 1
title: Data Extractor
description: Readme of Data Extractor
last_update:
  author: Aurelius
  date: 2025-11-23
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

## 📋 版本里程碑

### **v0.1.6 (2025/11/19)** - PDF 增强功能与内容深度提取

- ✨ **PDF 增强处理**: 新增增强版 PDF 处理器，支持图像、表格、数学公式的深度提取
- **🖼️ 图像提取**: 从 PDF 中提取图像并保存为本地文件或 base64 嵌入，支持尺寸调整和质量优化
- **📊 表格转换**: 智能识别 PDF 表格并转换为标准 Markdown 表格格式，保持数据结构完整性
- **🧮 公式提取**: 识别并提取 LaTeX 格式的数学公式，支持内联和块级公式格式保持
- **📝 结构化输出**: 自动生成包含提取资源的结构化 Markdown 文档，提供详细的提取统计信息
- **⚙️ 高级配置**: 新增 enhanced_options 参数，支持自定义输出目录、图像格式、质量控制等高级配置
- **📈 性能优化**: 提供详细的性能对比参考和故障排除指南，支持选择性功能启用
- **🔧 向后兼容**: 保持所有现有 API 的向后兼容性，新功能默认启用但可选择性关闭

### **v0.1.5 (2025/09/12)** - MCP 工具架构重构与标准化

- ✅ **MCP 工具标准化**: 全面重构 14 个 MCP 工具，统一使用 Annotated[*, Field(...)] 参数约束模式，提供清晰的参数描述和示例
- **核心重构**: 全面重构 14 个 MCP 工具，全面测试系统优化，从 BaseModel 子类实现迁移到 `Annotated[*, Field(...)]` 参数约束模式
- **参数标准化**: 统一参数定义规范，提供清晰的中文描述和示例说明
- **输出模式优化**: 增强响应模型描述，提升 MCP Client 兼容性
- **测试适配**: 全面更新测试用例，适配新的函数签名和参数传递方式
- **文档同步**: 更新 README.md 和测试文档，反映架构变更

### **v0.1.4 (2025/09/06)** - 基于 Scrapy + FastMCP 构建的企业级网页抓取 MCP Server

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

## 🎯 快速参考

- [用户指南](docs/6-User-Guide.md)
- [架构设计](docs/1-Framework.md)
- [开发指南](docs/2-Development.md)
- [测试指南](docs/3-Testing.md)
- [配置系统](docs/4-Configuration.md)
- [常用指令](docs/5-Commands.md)

## 🤝 贡献

欢迎提交 [Issue](https://github.com/ThreeFish-AI/data-extractor/issues) 和 Pull Request 来改进这个项目。

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**注意**: 请负责任地使用此工具，遵守网站的使用条款和 robots.txt 规则，尊重网站的知识产权。
