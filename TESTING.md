# 测试文档 - Data Extractor 核心引擎与 MCP 工具集

本文档详细说明了 Data Extractor 项目的测试架构、测试用例和自动化测试运行方法。

## 测试架构概览

### 测试目录结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # Pytest 配置和共享 fixtures
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_scraper.py         # WebScraper 核心引擎测试
│   ├── test_advanced_features.py # 高级功能测试 (反检测、表单处理)
│   └── test_utils.py           # 工具类测试 (限流、重试、缓存等)
├── integration/                # 集成测试
│   ├── __init__.py
│   └── test_mcp_tools.py       # 10个 MCP 工具集成测试
└── fixtures/                   # 测试数据和固定装置
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

### 10 个核心 MCP 工具测试覆盖

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
| MCP Tools              | 95%+       | 输入验证、错误响应           |
| 整体项目               | 90%+       | 端到端功能完整性             |

通过这套完整的测试体系，确保 Data Extractor 核心引擎和 MCP 工具集的稳定性、可靠性和性能表现。
