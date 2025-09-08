# 测试文档 - Data Extractor 核心引擎与 MCP 工具集

本文档详细说明了 Data Extractor 项目的测试架构、测试用例和自动化测试运行方法。

## 测试架构概览

### 测试目录结构

```
tests/
├── __init__.py                     # 测试包初始化
├── conftest.py                     # Pytest 配置和共享 fixtures
├── unit/                           # 单元测试
│   ├── __init__.py
│   ├── test_scraper.py             # WebScraper 核心引擎测试
│   ├── test_advanced_features.py   # 高级功能测试 (反检测、表单处理)
│   ├── test_utils.py               # 工具类测试 (限流、重试、缓存等)
│   ├── test_markdown_converter.py  # MarkdownConverter 测试
│   └── test_pdf_processor.py       # PDFProcessor 测试
├── integration/                    # 集成测试
│   ├── __init__.py
│   ├── test_mcp_tools.py           # 14 个 MCP 工具集成测试
│   └── test_comprehensive_integration.py  # 综合集成测试 (端到端、性能、实际场景)
└── fixtures/                       # 测试数据和固定装置
```

### 测试分类

1. **单元测试 (Unit Tests)**

- 测试独立模块和类的功能
- 使用 Mock 隔离外部依赖
- 快速执行，覆盖核心业务逻辑

2. **集成测试 (Integration Tests)**

- 测试 MCP 工具的端到端功能
- 验证组件间的交互
- 模拟真实使用场景
- 性能和负载测试
- 系统健康和诊断检查

## 核心引擎测试 (单元测试)

### WebScraper 引擎测试 (`test_scraper.py`)

#### DataExtractor 类测试

- **简单选择器提取**: 测试基本 CSS 选择器数据提取
- **多元素提取**: 测试 `multiple: true` 配置的多元素提取
- **属性提取**: 测试元素属性(href、src)提取
- **错误处理**: 测试不存在选择器的处理

#### WebScraper 核心类测试

- **初始化测试**: 验证配置正确加载
- **请求头生成**: 测试默认 HTTP 请求头生成
- **方法选择逻辑**: 测试自动方法选择 (auto/simple/scrapy/selenium)
- **URL 抓取**: 测试不同方法的网页抓取
- **批量抓取**: 测试多 URL 并发抓取
- **错误恢复**: 测试网络错误和异常处理
- **元数据提取**: 测试响应时间、内容长度等元数据提取

```python
# 示例测试用例
@pytest.mark.asyncio
async def test_scrape_url_simple_method(self, scraper, mock_http_response):
    """测试简单 HTTP 方法抓取"""
    with patch('requests.get') as mock_get:
        mock_get.return_value = mock_http_response

        result = await scraper.scrape_url("https://example.com", method="simple")

        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
```

### 高级功能测试 (`test_advanced_features.py`)

#### AntiDetectionScraper 反检测测试

- **Undetected Chrome**: 测试无痕 Chrome 浏览器抓取
- **Playwright 隐身**: 测试 Playwright 反检测抓取
- **人类行为模拟**: 测试鼠标移动、滚动等行为模拟
- **隐身设置应用**: 测试 CDP 命令和隐身脚本注入
- **错误处理**: 测试浏览器启动失败等异常场景

#### FormHandler 表单处理测试

- **基础表单填写**: 测试输入框、密码框填写
- **复杂表单元素**: 测试下拉选择框、复选框处理
- **表单提交**: 测试按钮点击和键盘提交
- **元素等待**: 测试 WebDriverWait 元素等待功能
- **错误恢复**: 测试元素未找到等异常处理

```python
# 示例测试用例
@pytest.mark.asyncio
async def test_fill_form_field_select(self, form_handler):
    """测试下拉选择框填写"""
    mock_element = Mock()
    mock_element.tag_name = "select"

    with patch('selenium.webdriver.support.ui.Select') as mock_select_class:
        await form_handler._fill_form_field(driver, "country", "US", mock_element)
        mock_select_class.return_value.select_by_visible_text.assert_called_once_with("US")
```

### 工具类测试 (`test_utils.py`)

#### RateLimiter 限流器测试

- **限流边界测试**: 测试请求频率限制
- **时间窗口清理**: 测试过期请求时间戳清理
- **并发限流**: 测试多请求并发限流效果

#### RetryManager 重试管理器测试

- **指数退避**: 测试退避延迟计算 (1s, 2s, 4s, 8s...)
- **重试成功**: 测试失败后重试成功场景
- **重试耗尽**: 测试最大重试次数耗尽处理
- **异常分类**: 测试不同异常的重试策略

#### CacheManager 缓存管理器测试

- **缓存设置获取**: 测试键值对存储和读取
- **TTL 过期**: 测试缓存生存时间过期清理
- **缓存未命中**: 测试不存在键的处理
- **缓存清空**: 测试全局缓存清理功能
- **键生成**: 测试 URL 和参数的哈希键生成

#### MetricsCollector 指标收集器测试

- **请求记录**: 测试 HTTP 方法、状态码、响应时间记录
- **错误统计**: 测试错误类型和数量统计
- **汇总统计**: 测试成功率、平均响应时间计算
- **指标重置**: 测试统计数据重置功能

#### 工具函数测试

- **URL 验证**: 测试 URL 格式验证 (http/https)
- **文本清理**: 测试 HTML 标签移除和空白符处理
- **配置验证**: 测试数据提取配置格式验证
- **计时装饰器**: 测试异步函数执行时间测量

```python
# 示例测试用例
def test_cache_expiration(self, temp_cache_dir):
    """测试缓存过期机制"""
    manager = CacheManager(cache_dir=temp_cache_dir)

    manager.set("expire_key", "value", ttl=0.1)  # 极短 TTL
    assert manager.get("expire_key") == "value"  # 立即可用

    time.sleep(0.2)  # 等待过期
    assert manager.get("expire_key") is None    # 过期后为空
```

## MCP 工具集成测试 (`test_mcp_tools.py`)

### 14 个核心 MCP 工具测试覆盖

#### 1. scrape_webpage - 单页面抓取

- **成功抓取**: 测试正常网页抓取返回数据结构
- **URL 验证**: 测试无效 URL 错误处理
- **方法验证**: 测试无效抓取方法错误处理
- **提取配置**: 测试自定义数据提取配置
- **异常处理**: 测试网络异常和工具异常处理

#### 2. scrape_multiple_webpages - 批量页面抓取

- **批量成功**: 测试多 URL 并发抓取
- **空列表处理**: 测试空 URL 列表错误处理
- **部分失败**: 测试部分 URL 无效时的处理
- **结果汇总**: 测试批量抓取结果统计

#### 3. extract_links - 链接提取

- **链接解析**: 测试 HTML 中 `<a>` 标签链接提取
- **域名过滤**: 测试 `filter_domains` 白名单过滤
- **域名排除**: 测试 `exclude_domains` 黑名单排除
- **去重处理**: 测试重复链接去除

#### 4. get_page_info - 页面信息获取

- **基础信息**: 测试标题、状态码、内容长度获取
- **元数据提取**: 测试响应时间、内容类型获取
- **错误页面**: 测试 404、500 等错误页面处理
- **重定向处理**: 测试 HTTP 重定向跟踪

#### 5. check_robots_txt - robots.txt 检查

- **robots.txt 存在**: 测试正常 robots.txt 解析
- **文件不存在**: 测试 404 状态处理
- **规则解析**: 测试 User-agent、Disallow、Allow 规则
- **爬虫友好性**: 测试爬取权限检查

#### 6. scrape_with_stealth - 反检测抓取

- **隐身方法**: 测试 undetected-chrome、playwright 方法
- **反检测特征**: 测试 User-Agent、Viewport 等反检测设置
- **JavaScript 渲染**: 测试动态内容抓取
- **方法验证**: 测试无效隐身方法错误处理

#### 7. fill_and_submit_form - 表单自动化

- **表单填写**: 测试各种表单字段填写
- **提交方式**: 测试按钮点击和键盘提交
- **等待元素**: 测试提交后页面元素等待
- **数据验证**: 测试空表单数据错误处理

#### 8. get_server_metrics - 服务器指标

- **性能指标**: 测试请求数、错误数、成功率统计
- **响应时间**: 测试平均响应时间计算
- **错误分类**: 测试超时、连接等错误分类统计
- **实时更新**: 测试指标实时更新机制

#### 9. clear_cache - 缓存清理

- **缓存清空**: 测试全局缓存清理功能
- **清理反馈**: 测试清理成功消息返回
- **异常处理**: 测试缓存清理异常处理
- **状态验证**: 测试清理后缓存状态验证

#### 10. extract_structured_data - 结构化数据提取

- **JSON-LD**: 测试 JSON-LD 格式结构化数据提取
- **微数据**: 测试 HTML 微数据格式提取
- **Open Graph**: 测试 OG 标签数据提取
- **数据类型**: 测试不同数据类型过滤 (all/jsonld/microdata/opengraph)

#### 11. convert_webpage_to_markdown - 页面转 Markdown

- **HTML 转换**: 测试完整 HTML 内容转换为 Markdown 格式
- **内容提取**: 测试主要内容区域智能提取功能
- **元数据处理**: 测试标题、描述、字数等元数据计算
- **URL 处理**: 测试相对 URL 转换为绝对 URL
- **自定义选项**: 测试自定义 Markdown 格式化选项
- **文本重构**: 测试从文本内容重构 HTML 的处理
- **错误处理**: 测试无效 URL 和抓取失败的错误处理

#### 12. batch_convert_webpages_to_markdown - 批量 Markdown 转换

- **批量处理**: 测试多个 URL 的并发转换处理
- **部分失败**: 测试部分 URL 失败时的错误处理
- **统计信息**: 测试成功/失败统计和成功率计算
- **空列表处理**: 测试空 URL 列表的错误处理
 - **图片嵌入参数**: 验证批量工具暴露 `embed_images` 与 `embed_options` 参数模式，确保与单页一致

#### 13. convert_pdf_to_markdown - PDF 转 Markdown

- **双引擎支持**: 测试 PyMuPDF 和 PyPDF2 两种 PDF 处理引擎
- **智能回退**: 测试 PyMuPDF 失败时自动切换到 PyPDF2
- **URL 和本地文件**: 测试 PDF URL 自动下载和本地文件处理
- **页面范围选择**: 测试部分页面提取功能 (page_range 参数)
- **元数据提取**: 测试作者、标题、创建日期等 PDF 元数据提取
- **输出格式**: 测试 Markdown 和纯文本两种输出格式
- **方法选择**: 测试 auto、pymupdf、pypdf2 三种方法选择
- **错误处理**: 测试文件不存在、下载失败、解析错误等异常场景

#### 14. batch_convert_pdfs_to_markdown - 批量 PDF 转换

- **并发处理**: 测试多个 PDF 文件的并发转换能力
- **混合结果**: 测试成功和失败混合的批量处理结果
- **统计摘要**: 测试总数、成功数、失败数、总页数、总字数等统计信息
- **错误隔离**: 测试单个 PDF 失败不影响其他文件处理
- **异常处理**: 测试批量处理中的异常捕获和处理
- **空列表处理**: 测试空 PDF 列表的错误处理
- **资源管理**: 测试临时文件清理和内存管理
- **无效 URL**: 测试包含无效 URL 的批量处理
- **配置一致性**: 测试批量处理中的配置一致性

## Markdown 转换器单元测试 (`test_markdown_converter.py`)

### MarkdownConverter 核心类测试

#### 1. 初始化和配置测试

- **默认配置**: 测试 MarkdownConverter 默认选项设置
- **配置验证**: 测试标题样式、列表符号、链接格式等配置项

#### 2. HTML 预处理功能测试

- **注释移除**: 测试 HTML 注释的清理功能
- **标签清理**: 测试 script、style、nav、header 等无关标签移除
- **URL 转换**: 测试相对 URL 转换为绝对 URL 功能
- **空元素清理**: 测试空的 p 和 div 标签移除

#### 3. HTML 到 Markdown 转换测试

- **基础转换**: 测试标题、段落、链接、图片的基本转换
- **列表处理**: 测试有序和无序列表的 Markdown 转换
- **自定义选项**: 测试自定义 Markdown 格式化选项
- **错误处理**: 测试转换过程中的异常处理

#### 4. Markdown 后处理测试

- **空行清理**: 测试多余空白行的清理功能
- **列表格式**: 测试列表格式的优化处理
- **空格清理**: 测试行尾空格和制表符的清理
- **内容修剪**: 测试开头结尾空白字符的清理

#### 5. 内容区域提取测试

- **主要标签**: 测试 main、article 标签的内容提取
- **类选择器**: 测试 .content、.post 等类选择器提取
- **回退机制**: 测试找不到主要内容时回退到 body 的处理
- **最小长度**: 测试内容最小长度要求的验证

#### 6. 完整转换流程测试

- **HTML 内容**: 测试包含完整 HTML 内容的网页转换
- **文本重构**: 测试仅有文本内容时的 HTML 重构转换
- **元数据包含**: 测试元数据的计算和包含功能
- **配置选项**: 测试各种转换配置选项的应用

#### 7. 批量转换测试

- **成功转换**: 测试多个页面的成功批量转换
- **部分失败**: 测试部分页面失败时的处理逻辑
- **统计计算**: 测试成功率和统计信息的计算
- **异常处理**: 测试批量转换过程中的异常捕获

#### 8. 高级格式化功能测试 (TestAdvancedFormattingFeatures)

- **表格格式化**: 测试表格对齐和格式统一化功能
  - 基础表格格式化：标准化单元格间距和对齐方式
  - 对齐识别：自动检测和应用左对齐、居中、右对齐格式
  - 分隔符优化：规范化表格分隔符格式
- **代码块增强**: 测试自动语言检测和代码块格式化
  - 语言检测：自动识别 JavaScript、Python、HTML、SQL、JSON 等语言
  - 格式标准化：确保代码块正确标记和分隔
  - 多语言支持：支持 10+ 种编程语言的自动识别
- **引用块优化**: 测试引用格式的标准化和美化
  - 间距统一：确保引用块前后有适当空行间距
  - 格式规范：统一引用符号和缩进格式
- **图片描述增强**: 测试图片 alt 文本的自动生成和优化
  - 文件名解析：从图片文件名自动生成描述性文本
  - 格式美化：将下划线、连字符转换为友好的描述文本
  - 缺失文本补充：为缺少 alt 文本的图片生成合适描述
- **链接格式优化**: 测试链接格式的规范化和修复
  - 空格清理：移除链接文本和 URL 中的多余空格
  - 跨行修复：修复因换行导致的链接格式问题
  - 格式统一：确保所有链接使用一致的 Markdown 格式
- **列表格式化**: 测试列表标记的统一化和格式优化
  - 标记统一：统一使用相同的列表标记符号
  - 间距规范：确保列表项之间有适当间距
  - 嵌套处理：正确处理多层嵌套列表格式
- **标题优化**: 测试标题层级和间距的自动优化
  - 间距添加：在标题前后自动添加空行
  - 层级检查：验证标题层级结构的合理性
  - 格式统一：确保所有标题使用一致的格式
- **排版增强**: 测试智能排版功能
  - 智能引号：自动转换直引号为弯引号
  - 破折号转换：将双连字符转换为 em 破折号
  - 空格优化：清理多余空格和标点符号间距
  - 标点修正：修复标点符号周围的空格问题
- **配置管理测试**: 测试格式化选项的配置功能
  - 选择性启用：测试单独启用/禁用各项格式化功能
  - 配置传递：测试格式化选项在转换流程中的正确传递
  - 默认行为：验证各选项的默认启用状态
- **集成测试**: 测试格式化功能与转换流程的集成
  - 单页转换：测试带格式化选项的单页面转换
  - 批量转换：测试批量转换中格式化选项的应用
  - 错误处理：测试格式化过程中的异常处理和恢复
- **边界情况测试**: 测试异常输入的处理
  - 空内容处理：测试空字符串和 None 值的处理
  - 恶意内容：测试包含特殊字符的内容处理
  - 性能测试：测试大量内容的格式化性能

#### 9. 图片嵌入测试 (TestImageEmbedding)

- **小图嵌入**: 模拟 `requests.get` 返回小图片，验证被转换为 `data:image/*;base64,` 数据 URI 并统计 `embedded=1`
- **大图跳过**: 当 `Content-Length` 或实际内容超过 `max_bytes_per_image` 时，应跳过嵌入并统计 `skipped_large=1`
- **转换流程集成**: 在 `convert_webpage_to_markdown(..., embed_images=True, embed_options={...})` 下，验证返回的 `markdown` 含 data URI，`conversion_options.embed_images=true`，且 `metadata.image_embedding` 包含统计信息

```python
# 示例集成测试用例
@pytest.mark.asyncio
async def test_scrape_webpage_with_extraction_config(self, sample_scrape_result):
    \"\"\"测试带提取配置的网页抓取\"\"\"
    extraction_config = {\"title\": \"h1\", \"content\": \"p\"}

    with patch('extractor.server.web_scraper') as mock_scraper:
        mock_scraper.scrape_url.return_value = sample_scrape_result

        result = await scrape_webpage(
            url=\"https://example.com\",
            method=\"simple\",
            extract_config=extraction_config
        )

        assert result[\"success\"] is True
        mock_scraper.scrape_url.assert_called_once_with(
            url=\"https://example.com\",
            method=\"simple\",
            extract_config=extraction_config,
            wait_for_element=None
        )
```

## PDF 处理器单元测试 (`test_pdf_processor.py`)

### PDFProcessor 核心类测试

#### 1. 初始化和配置测试

- **初始化验证**: 测试 PDFProcessor 实例的正确创建和配置
- **支持方法检查**: 验证支持的 PDF 处理方法 (pymupdf, pypdf2, auto)
- **临时目录创建**: 测试临时目录的创建和权限设置

#### 2. URL 检测和文件下载测试

- **URL 格式验证**: 测试 `_is_url()` 方法对各种 URL 格式的识别
  - HTTP/HTTPS URL 识别
  - 本地路径识别
  - 无效格式处理
- **PDF 下载功能**: 测试从 URL 下载 PDF 文件的功能
  - 成功下载测试
  - HTTP 错误处理 (404, 500 等)
  - 网络异常处理
  - 临时文件创建和存储

#### 3. PDF 提取引擎测试

**PyMuPDF (fitz) 引擎测试**:

- **基础提取**: 测试文本内容的基本提取功能
- **页面范围**: 测试指定页面范围的部分提取
- **元数据提取**: 测试 PDF 元数据 (标题、作者、创建日期) 的提取
- **错误处理**: 测试损坏或无效 PDF 文件的处理

**PyPDF2 引擎测试**:

- **文本提取**: 测试 PyPDF2 引擎的文本提取能力
- **元数据处理**: 测试元数据字段的正确解析和转换
- **页面处理**: 测试多页文档的页面迭代处理
- **异常捕获**: 测试 PDF 解析异常的处理机制

#### 4. 智能方法选择测试 (auto 模式)

- **优先级测试**: 测试 PyMuPDF → PyPDF2 的自动选择优先级
- **故障转移**: 测试主方法失败时的自动切换机制
- **完全失败**: 测试两个引擎都失败时的错误处理
- **方法记录**: 验证最终使用的方法正确记录在结果中

#### 5. Markdown 转换测试

- **文本清理**: 测试原始 PDF 文本的清理和格式化
- **标题识别**: 测试大写文本和结尾冒号的标题识别
- **格式优化**: 测试 Markdown 格式的优化处理
- **空内容处理**: 测试空文本内容的处理逻辑

#### 6. 批量处理测试

- **并发处理**: 测试多个 PDF 文件的并发处理能力
- **错误容错**: 测试部分文件失败时的整体处理逻辑
- **统计计算**: 测试成功/失败统计和汇总信息的计算
- **异常处理**: 测试批量处理过程中的异常捕获和处理

#### 7. 资源管理测试

- **文件清理**: 测试临时文件的自动清理机制
- **内存管理**: 验证 PDF 处理过程中的内存使用优化
- **目录清理**: 测试临时目录的完整清理功能
- **异常安全**: 测试异常情况下的资源释放保证

#### 8. 验证和错误处理测试

- **参数验证**: 测试输入参数的格式验证和错误提示
- **文件存在**: 测试本地 PDF 文件存在性的检查
- **页面范围**: 测试页面范围参数的合法性验证
- **输出格式**: 测试输出格式 (markdown/text) 的验证

### PDF MCP 工具集成测试

#### convert_pdf_to_markdown 工具测试

- **参数验证**: 测试方法、输出格式、页面范围等参数的验证
- **本地文件**: 测试本地 PDF 文件路径的处理
- **URL 处理**: 测试 PDF URL 的下载和处理流程
- **错误响应**: 测试各种错误情况的响应格式统一性

#### batch_convert_pdfs_to_markdown 工具测试

- **批量验证**: 测试 PDF 源列表的验证逻辑
- **并发处理**: 验证批量处理的性能和准确性
- **混合结果**: 测试成功和失败混合结果的处理
- **统计报告**: 验证批量处理统计信息的准确性

## 综合集成测试 (`test_comprehensive_integration.py`)

### 端到端功能测试

#### 1. TestComprehensiveIntegration - 综合功能测试

- **完整转换流程**: 测试从网页抓取到 Markdown 转换的完整流程
- **高级格式化集成**: 测试所有格式化功能的协同工作
- **真实网站测试**: 测试实际新闻文章、技术博客的转换效果
- **批量转换工作流**: 测试混合成功/失败结果的批量处理
- **配置动态应用**: 测试转换过程中配置选项的动态应用

```python
@pytest.mark.asyncio
async def test_full_markdown_conversion_pipeline(self, mock_successful_scrape_result):
    """测试完整的 Markdown 转换流程"""
    tools = await app.get_tools()
    convert_tool = tools["convert_webpage_to_markdown"]

    # 执行端到端转换测试
    with patch('extractor.server.web_scraper') as mock_scraper:
        mock_scraper.scrape_url.return_value = mock_successful_scrape_result
        result = await convert_tool.fn(
            url="https://example.com/article",
            formatting_options={"format_tables": True, "apply_typography": True}
        )
        assert result["success"] is True
        assert "conversion_result" in result
```

#### 2. TestPerformanceAndLoad - 性能与负载测试

- **并发性能测试**: 测试同时处理 20 个 URL 的并发能力
- **大内容处理**: 测试大型网页内容的转换性能
- **内存使用监控**: 测试长时间运行的内存稳定性
- **响应时间测试**: 测试各种场景下的响应时间要求
- **系统资源监控**: 测试 CPU 和内存资源使用情况

```python
@pytest.mark.asyncio
async def test_performance_under_load(self):
    """测试系统负载性能"""
    start_time = time.time()

    # 创建 20 个并发任务
    tasks = []
    for i in range(20):
        task = self._simulate_conversion_task(f"https://example{i}.com")
        tasks.append(task)

    # 并发执行并测量性能
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start_time

    # 验证性能要求
    assert duration < 30.0  # 20个任务在30秒内完成
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    assert success_count >= 18  # 至少90%成功率
```

#### 3. TestErrorResilienceAndRecovery - 错误恢复与韧性测试

- **网络错误处理**: 测试网络超时、连接失败的恢复能力
- **部分失败处理**: 测试批量操作中部分失败的处理逻辑
- **资源耗尽恢复**: 测试系统资源不足时的自动恢复
- **异常场景覆盖**: 测试各种异常情况下的系统稳定性
- **故障转移机制**: 测试组件故障时的自动切换能力

#### 4. TestRealWorldScenarios - 真实场景测试

- **新闻文章转换**: 测试复杂新闻网站的内容提取和格式化
- **技术博客处理**: 测试包含代码块的技术内容转换
- **电商页面测试**: 测试产品页面的结构化数据提取
- **多媒体内容**: 测试包含图片、视频的页面处理
- **多语言支持**: 测试中文、英文等多语言内容处理

````python
@pytest.mark.asyncio
async def test_news_article_conversion(self):
    """测试新闻文章的真实转换场景"""
    # 模拟复杂的新闻网站结构
    news_html = self._create_complex_news_html()

    converter = MarkdownConverter()
    result = converter.convert_webpage_to_markdown({
        "url": "https://news-example.com/article",
        "content": {"html": news_html, "text": "Extracted text content"},
        "title": "Breaking News: Technology Advances",
        "meta_description": "Latest news in technology sector"
    })

    # 验证转换质量
    markdown = result["markdown"]
    assert "# Breaking News: Technology Advances" in markdown
    assert "## " in markdown  # 应包含副标题
    assert "|" in markdown    # 应包含表格
    assert "```" in markdown  # 应包含代码块
````

#### 5. TestConfigurationFlexibility - 配置灵活性测试

- **动态配置切换**: 测试运行时配置选项的动态切换
- **配置参数验证**: 测试各种配置参数组合的有效性
- **默认配置测试**: 测试默认配置下的系统行为
- **配置冲突处理**: 测试相互冲突配置的处理逻辑
- **配置持久性测试**: 测试配置在不同操作间的持久性

### TestSystemHealthAndDiagnostics - 系统健康诊断

#### 组件初始化验证

- **服务器组件检查**: 验证所有核心组件正确初始化
- **工具注册完整性**: 确保所有 14 个 MCP 工具正确注册
- **依赖关系验证**: 检查组件间依赖关系的正确性
- **配置一致性检查**: 验证系统配置的一致性和有效性

#### 系统韧性测试

- **并发访问测试**: 测试多个客户端同时访问的稳定性
- **长期运行测试**: 测试系统长期运行的稳定性
- **资源泄漏检测**: 监控和检测潜在的内存泄漏
- **故障恢复能力**: 测试系统从故障状态的自动恢复能力

#### 工具参数模式完整性

## 强化集成测试套件

为了补强集成测试的覆盖范围和真实性，新增了以下三个专门的集成测试套件：

### PDF 工具深度集成测试 (`test_pdf_integration.py`)

**TestPDFToolsIntegration** - PDF 工具实际调用验证

- **实际工具执行**: 测试通过 MCP 接口直接调用 PDF 转换工具
- **双引擎验证**: 测试 PyMuPDF 和 PyPDF2 引擎的实际调用和回退机制
- **参数传递验证**: 测试页面范围、输出格式等参数的正确传递
- **错误处理集成**: 测试文件不存在、解析失败等错误的完整处理流程
- **并发调用测试**: 测试多个 PDF 工具的并发执行稳定性

**TestPDFIntegrationWithRealProcessing** - 真实处理场景测试

- **临时文件处理**: 测试使用真实临时文件的 PDF 处理流程
- **混合批处理**: 测试存在和不存在文件混合的批量处理
- **URL 下载集成**: 测试 PDF URL 下载和处理的完整流程
- **内存使用监控**: 测试 PDF 处理过程中的内存使用和清理
- **无效配置处理**: 测试各种无效配置参数的处理

### 跨工具协同集成测试 (`test_cross_tool_integration.py`)

**TestCrossToolIntegration** - 多工具协同测试

- **页面-PDF 工作流**: 测试抓取网页 → 发现 PDF→ 处理 PDF 的完整工作流
- **批量协同处理**: 测试批量网页抓取和批量 PDF 处理的组合使用
- **跨工具指标收集**: 测试多个工具使用后的综合指标收集
- **错误传播验证**: 测试一个工具失败对其他工具的影响
- **资源共享管理**: 测试多工具间的资源清理和内存管理
- **并发多工具**: 测试不同工具的并发执行和互不干扰

**TestRealWorldIntegrationScenarios** - 真实世界使用场景

- **研究论文收集**: 测试学术网站的论文发现和批量下载转换
- **网站文档备份**: 测试完整网站文档的抓取和 Markdown 转换
- **竞品分析工作流**: 测试多竞品网站的批量分析和资源提取

### 端到端现实场景测试 (`test_end_to_end_integration.py`)

**TestEndToEndRealWorldScenarios** - 端到端现实场景

- **完整文档处理管道**: 模拟真实的研究门户处理，包含网页抓取、Markdown 转换、PDF 批处理
- **网络延迟模拟**: 测试各种网络条件下的系统表现
- **大型内容处理**: 测试处理大型文档和复杂网页结构
- **Unicode 兼容性**: 测试多语言内容的完整处理流程

**TestEndToEndErrorRecovery** - 错误恢复和韧性测试

- **网络重试机制**: 测试网络间歇性故障的自动重试和恢复
- **部分失败处理**: 测试批量操作中部分失败的优雅降级
- **资源耗尽恢复**: 测试内存不足等资源问题的处理
- **边界条件测试**: 测试空内容、恶意内容、格式错误等边界情况

**TestEndToEndPerformance** - 性能基准测试

- **大文档处理**: 测试 50 页 PDF 等大型文档的处理性能
- **高并发负载**: 测试 20 个并发任务的系统性能表现
- **内存效率**: 测试长时间运行的内存使用效率
- **网络效率**: 测试不同网络延迟下的处理效率

**TestEndToEndDataIntegrity** - 数据一致性验证

- **Unicode 字符保持**: 测试多语言字符在整个处理流程中的完整性
- **大数据一致性**: 测试大量数据处理的前后一致性
- **跨平台兼容**: 测试不同文件路径格式的兼容性处理
- **并发数据完整**: 测试并发处理中数据不被破坏

- **参数模式验证**: 确保所有工具具有正确的参数模式
- **描述信息检查**: 验证工具描述信息的完整性和准确性
- **模式结构验证**: 检查工具模式的结构完整性
- **参数类型验证**: 验证参数类型定义的正确性

```python
@pytest.mark.asyncio
async def test_system_resilience_under_load(self):
    """测试系统负载韧性"""
    # 并发访问多个工具
    tasks = []
    for tool_name in ["scrape_webpage", "convert_webpage_to_markdown", "get_server_metrics"]:
        task = app.get_tool(tool_name)
        tasks.append(task)

    # 验证并发访问的稳定性
    results = await asyncio.gather(*tasks)
    for result in results:
        assert result is not None
        assert hasattr(result, "name")
```

### TestMemoryAndResourceManagement - 内存和资源管理测试

#### 内存管理测试

- **内存泄漏检测**: 通过重复操作检测内存泄漏
- **垃圾回收验证**: 验证对象正确被垃圾回收
- **内存使用边界**: 测试内存使用的合理边界
- **大对象处理**: 测试大型内容对象的内存管理

#### 资源清理测试

- **文件句柄管理**: 确保文件句柄正确关闭
- **网络连接清理**: 验证网络连接正确释放
- **缓存清理机制**: 测试缓存的自动清理功能
- **临时资源清理**: 验证临时资源的及时清理

```python
@pytest.mark.asyncio
async def test_memory_and_resource_management(self):
    """测试内存和资源管理"""
    import gc

    initial_objects = len(gc.get_objects())

    # 重复创建和使用转换器
    for i in range(10):
        converter = MarkdownConverter()
        html = f"<html><body><h1>Test {i}</h1><p>Content {i}</p></body></html>"
        markdown = converter.html_to_markdown(html)
        assert "Test" in markdown
        del converter

    gc.collect()
    final_objects = len(gc.get_objects())
    object_growth = final_objects - initial_objects

    # 验证没有严重内存泄漏
    assert object_growth < 1000, f"Memory leak detected: {object_growth} new objects"
```

## 测试配置与固定装置 (`conftest.py`)

### 共享 Fixtures

#### 配置 Fixtures

- **test_config**: 安全的测试配置，禁用 JavaScript、减少并发
- **temp_cache_dir**: 临时缓存目录，测试后自动清理

#### Mock Fixtures

- **mock_web_scraper**: 模拟 WebScraper 实例
- **mock_anti_detection_scraper**: 模拟反检测抓取器
- **mock_form_handler**: 模拟表单处理器
- **mock_http_response**: 模拟 HTTP 响应对象

#### 测试数据 Fixtures

- **sample_html**: 标准 HTML 测试内容
- **sample_extraction_config**: 标准数据提取配置
- **sample_scrape_result**: 标准抓取结果数据结构

```python
@pytest.fixture
def test_config():
    \"\"\"安全的测试配置\"\"\"
    return DataExtractorSettings(
        server_name=\"Test Data Extractor\",
        enable_javascript=False,        # 禁用 JS 避免浏览器启动
        concurrent_requests=1,          # 单线程避免竞态条件
        browser_timeout=10,             # 短超时时间
        max_retries=2,                  # 减少重试次数
        rate_limit_requests_per_minute=60
    )
```

## 运行测试指南

### 环境准备

#### 1. 安装测试依赖

```bash
# 安装开发依赖 (包含 pytest)
uv sync --extra dev

# 或者使用 pip
pip install pytest pytest-asyncio
```

#### 2. 配置测试环境

```bash
# 复制环境配置 (测试会使用默认配置)
cp .env.example .env

# 确保测试配置禁用外部服务
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
export DATA_EXTRACTOR_CONCURRENT_REQUESTS=1
```

### 执行测试命令

#### 运行全部测试

```bash
# 运行所有测试
uv run pytest

# 详细输出模式
uv run pytest -v

# 显示覆盖率
uv run pytest --cov=extractor --cov-report=html
```

#### 运行特定测试类别

```bash
# 只运行单元测试
uv run pytest tests/unit/

# 只运行集成测试
uv run pytest tests/integration/

# 运行特定测试文件
uv run pytest tests/unit/test_scraper.py

# 运行特定测试类
uv run pytest tests/unit/test_scraper.py::TestWebScraper

# 运行特定测试方法
uv run pytest tests/unit/test_scraper.py::TestWebScraper::test_scraper_initialization
```

#### 高级测试选项

```bash
# 并行测试 (需要 pytest-xdist)
uv run pytest -n 4

# 失败时停止
uv run pytest -x

# 重新运行失败的测试
uv run pytest --lf

# 显示最慢的10个测试
uv run pytest --durations=10

# 生成 JUnit XML 报告
uv run pytest --junitxml=test-results.xml
```

### 测试报告分析

#### 覆盖率报告

```bash
# 生成 HTML 覆盖率报告
uv run pytest --cov=extractor --cov-report=html

# 查看报告
open htmlcov/index.html
```

#### 性能分析

```bash
# 测试执行时间分析
uv run pytest --durations=0

# 内存使用分析 (需要 pytest-monitor)
uv run pytest --monitor
```

## 测试最佳实践

### 1. 测试隔离原则

- 每个测试独立运行，不依赖其他测试
- 使用 fixtures 提供清洁的测试环境
- 避免修改全局状态

### 2. Mock 使用策略

- 外部服务调用 (HTTP 请求、浏览器) 必须 Mock
- 文件系统操作使用临时目录
- 时间相关测试使用时间 Mock

### 3. 异步测试注意事项

- 使用 `@pytest.mark.asyncio` 标记异步测试
- 确保 async/await 正确使用
- 避免异步测试中的竞态条件

### 4. 错误测试覆盖

- 测试异常情况和边界条件
- 验证错误消息和错误类型
- 测试资源清理和恢复

### 5. 数据驱动测试

```python
@pytest.mark.parametrize(\"url,expected\", [
    (\"https://example.com\", True),
    (\"http://test.org\", True),
    (\"not-a-url\", False),
])
def test_url_validation(url, expected):
    validator = URLValidator()
    assert validator.is_valid(url) == expected
```

## 持续集成配置

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12, 3.13]

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest --cov=extractor --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 故障排除

### 常见问题

#### 1. 浏览器相关测试失败

```bash
# 确保禁用 JavaScript 测试
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false

# 或在测试配置中设置
pytest -k "not selenium and not playwright"
```

#### 2. 网络相关测试失败

```bash
# 确保所有外部调用都被 Mock
pytest --disable-warnings -v
```

#### 3. 缓存相关测试失败

```bash
# 清理缓存目录
rm -rf /tmp/test_cache_*
```

#### 4. 异步测试超时

```bash
# 增加异步测试超时时间
pytest --asyncio-mode=auto --timeout=30
```

### 调试技巧

```python
# 在测试中使用 pdb 调试
import pdb; pdb.set_trace()

# 使用 pytest 调试模式
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

## 测试覆盖目标

| 组件                   | 目标覆盖率 | 关键测试点                   |
| ---------------------- | ---------- | ---------------------------- |
| WebScraper             | 95%+       | 方法选择、数据提取、错误处理 |
| AntiDetectionScraper   | 90%+       | 隐身功能、行为模拟           |
| FormHandler            | 90%+       | 表单元素识别、提交逻辑       |
| Utils (RateLimiter 等) | 95%+       | 边界条件、并发安全           |
| MarkdownConverter      | 95%+       | HTML 转换、格式化、批量处理  |
| MCP Tools              | 95%+       | 输入验证、错误响应           |
| 集成测试 (端到端)      | 90%+       | 完整工作流、性能、韧性       |
| 整体项目               | 92%+       | 端到端功能完整性             |

### 集成测试统计与覆盖详情

#### 原有集成测试覆盖

##### MCP 工具集成测试 (`test_mcp_tools.py`)

- **工具注册验证**: 确保所有 14 个 MCP 工具正确注册
- **工具结构检查**: 验证工具属性、描述、参数模式完整性
- **Markdown 转换集成**: 测试 Markdown 转换工具的集成功能
- **系统健康诊断**: 验证系统组件初始化和基本功能

##### 综合集成测试 (`test_comprehensive_integration.py`)

- **端到端工作流**: 从网页抓取到 Markdown 转换的完整流程测试
- **性能负载测试**: 并发处理、响应时间、系统资源使用测试
- **错误恢复韧性**: 网络故障、部分失败、异常处理测试
- **真实场景模拟**: 新闻网站、技术博客、多媒体内容测试
- **配置灵活性**: 动态配置、参数验证、默认行为测试
- **系统诊断监控**: 内存管理、资源清理、长期稳定性测试

#### 新增集成测试强化 (强化后新增 56 项测试)

##### PDF 工具深度集成测试 (`test_pdf_integration.py`) - 13 项测试

- **PDF 工具实际执行验证**: 通过 MCP 接口调用 PDF 处理工具，验证实际工作流
- **双引擎切换测试**: 验证 PyMuPDF 和 PyPDF2 引擎的自动选择和故障转移
- **参数传递完整性**: 测试 URL、页面范围、输出格式等参数的正确传递
- **错误处理和恢复**: 测试 PDF 下载失败、解析错误等异常情况的处理
- **并发执行验证**: 验证多个 PDF 并发处理时的资源管理和结果正确性

##### 跨工具协作集成测试 (`test_cross_tool_integration.py`) - 9 项测试

- **网页 →PDF→Markdown 工作流**: 测试从网页抓取到 PDF 转换到 Markdown 的完整流程
- **批量处理组合**: 验证多种工具的批量处理能力和数据流完整性
- **工具间参数传递**: 测试工具间配置和参数的正确传递
- **跨工具错误传播**: 验证一个工具失败对整个工作流的影响和恢复能力
- **指标收集集成**: 测试跨工具使用时的性能指标收集和汇总

##### 端到端现实场景测试 (`test_end_to_end_integration.py`) - 34 项测试

包含四大测试类，模拟真实使用场景:

1. **完整文档处理管道 (TestCompleteDocumentProcessingPipeline)** - 12 项测试

   - 技术文档门户完整处理流程
   - 学术论文研究工作流
   - 新闻聚合和内容提取
   - 企业知识库构建流程

2. **错误恢复和韧性测试 (TestErrorRecoveryAndResilience)** - 8 项测试

   - 网络中断恢复测试
   - 部分失败场景处理
   - 超时和重试机制验证
   - 资源清理验证

3. **性能和可扩展性基准测试 (TestPerformanceAndScalabilityBenchmarks)** - 8 项测试

   - 并发处理性能基准
   - 大量数据批处理测试
   - 内存使用监控和优化
   - 响应时间性能验证

4. **数据完整性和一致性验证 (TestDataIntegrityAndConsistency)** - 6 项测试
   - 跨工具数据一致性检查
   - 编码和格式完整性验证
   - 元数据传递完整性测试
   - 并发安全性验证

#### 测试质量提升成果

- **测试覆盖率**: 从 37 项集成测试提升到 93 项 (增长 151%)
- **通过率**: 当前 216/219 项通过 (98.6% 通过率)，3 项跳过
- **场景覆盖**: 新增现实场景模拟、跨工具协作、性能基准测试
- **错误处理**: 强化边界条件和异常情况测试覆盖
- **性能验证**: 新增并发执行、内存管理、响应时间测试

#### 最新测试执行结果 (v0.1.4)

**执行时间**: 2025-09-06
**总测试数**: 219 个  
**通过**: 216 个  
**跳过**: 3 个  
**失败**: 0 个  
**通过率**: 98.6%  
**执行耗时**: 47.92 秒

**跳过的测试**: 主要为网络依赖的下载测试，在单元测试环境中适当跳过

**测试系统稳定性**: 通过版本管理系统重构和 PDF 处理器延迟导入机制修复，解决了所有 27 个集成测试失败问题，系统测试稳定性和可靠性得到显著提升。

#### 测试质量保证

- **测试隔离性**: 每个测试独立执行，无状态依赖
- **Mock 策略**: 外部依赖完全隔离，确保测试稳定性
- **异常覆盖**: 全面测试错误情况和边界条件
- **性能基准**: 建立性能基准，确保系统响应要求
- **资源监控**: 监控内存泄漏、资源使用、垃圾回收效果

通过这套完整的测试体系，确保 Data Extractor 核心引擎和 MCP 工具集的稳定性、可靠性和性能表现。
