---
id: testing
sidebar_position: 3
title: Testing
description: Comprehensive Testing Guide and Quality Assurance
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - Testing
  - Quality Assurance
  - Test Coverage
  - CI/CD
---

本文档提供 Data Extractor 项目的完整测试指南，涵盖测试架构、自动化测试、手动测试、报告汇总和质量分析等全方位内容。

## 概述

Data Extractor 项目建立了完整的测试体系，包括单元测试、集成测试、性能测试和端到端测试。测试覆盖所有核心功能模块，确保代码质量和系统稳定性。

**测试体系特点**：

- **高覆盖率**：整体测试覆盖率达 98%+
- **多层次测试**：单元测试 → 集成测试 → 端到端测试
- **自动化执行**：完整的 CI/CD 集成和自动化测试流程
- **详细报告**：HTML、JSON、XML 等多格式测试报告
- **性能监控**：内存使用、响应时间、并发性能监控

**测试金字塔**：

- **单元测试 (70%)**: 测试单个函数和类
- \*\*集成测试 (25%): 测试模块间交互
- **端到端测试 (5%)**: 测试完整业务流程

**测试标记**：

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.requires_network`: 需要网络访问
- `@pytest.mark.requires_browser`: 需要浏览器环境

## 测试架构

### 测试目录结构

```
tests/
├── __init__.py                     # 测试包初始化
├── conftest.py                     # Pytest 配置和共享 fixtures
├── README.md                       # 测试说明文档
├── unit/                           # 单元测试
│   ├── __init__.py
│   ├── test_config.py              # 配置系统测试
│   ├── test_scraper.py             # 网页抓取引擎测试
│   ├── test_scraper_simple.py      # 简单抓取器测试
│   ├── test_advanced_features.py   # 高级功能测试
│   ├── test_utils.py               # 工具类测试
│   ├── test_utils_basic.py         # 基础工具测试
│   ├── test_markdown_converter.py  # Markdown 转换器测试
│   ├── test_pdf_processor.py       # PDF 处理器测试
│   ├── test_enhanced_pdf_processor.py # 增强PDF处理器测试
│   └── test_server_mcp_tools.py    # MCP 服务器工具测试
├── integration/                    # 集成测试
│   ├── __init__.py
│   ├── test_mcp_tools.py           # MCP 工具集成测试
│   ├── test_updated_mcp_tools.py   # 更新的 MCP 工具测试
│   ├── test_comprehensive_integration.py # 综合集成测试
│   ├── test_updated_comprehensive_integration.py # 更新的综合集成测试
│   ├── test_cross_tool_integration.py # 跨工具集成测试
│   ├── test_end_to_end_integration.py # 端到端集成测试
│   ├── test_pdf_integration.py     # PDF 集成测试
│   └── test_langchain_blog_conversion.py # 实际网站转换测试
└── reports/                        # 测试报告存储
    ├── test-report.html            # 主测试报告
    ├── unit-test-report.html       # 单元测试报告
    ├── integration-test-report.html # 集成测试报告
    ├── performance-test-report.html # 性能测试报告
    ├── full-test-results.json      # 完整测试结果
    ├── unit-test-results.json      # 单元测试结果
    ├── integration-test-results.json # 集成测试结果
    └── htmlcov/                    # 覆盖率 HTML 报告
```

### 测试分类体系

#### 1. 单元测试 (Unit Tests)

- **目标**：测试独立模块和类的功能
- **特点**：快速执行、使用 Mock 隔离外部依赖、高代码覆盖率
- **覆盖范围**：配置系统、网页抓取器、PDF 处理器、工具类等

```python
import pytest
from unittest.mock import AsyncMock, patch
from extractor.config import settings

class TestDataExtractor:
    """测试数据提取器"""

    def test_initialization(self):
        """测试初始化"""
        extractor = DataExtractor(settings)
        assert extractor.config is settings
        assert extractor._cache == {}

    @pytest.mark.asyncio
    async def test_extract_data_success(self):
        """测试成功数据提取"""
        extractor = DataExtractor(settings)
        result = await extractor.extract_data("https://example.com")

        assert "url" in result
        assert "data" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_extract_data_invalid_url(self):
        """测试无效URL"""
        extractor = DataExtractor(settings)

        with pytest.raises(ValueError, match="URL cannot be empty"):
            await extractor.extract_data("")
```

#### 2. 集成测试 (Integration Tests)

- **目标**：验证多个组件之间的协作
- **特点**：真实组件交互、端到端工作流验证
- **覆盖范围**：MCP 工具集成、跨工具协作、真实场景模拟

```python
import pytest
from extractor.server import app

@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_scraping_integration():
    """测试网页抓取集成"""
    result = await app.scrape_webpage(
        url="https://httpbin.org/html",
        extract_config={"title": "h1"}
    )

    assert result.success is True
    assert "data" in result
```

#### 3. 性能测试 (Performance Tests)

- **目标**：评估系统在负载下的表现
- **特点**：并发处理测试、内存使用监控、响应时间验证
- **覆盖范围**：批量处理、大文档处理、长期稳定性

#### 4. 端到端测试 (E2E Tests)

- **目标**：验证完整的业务流程
- **特点**：真实环境模拟、完整工作流测试
- **覆盖范围**：文档处理管道、错误恢复、数据一致性

## 自动化测试

### 测试运行脚本

项目提供了综合的测试运行脚本 `scripts/run-tests.sh`，支持多种测试模式：

```bash
# 运行完整测试套件（默认）
./scripts/run-tests.sh

# 运行单元测试
./scripts/run-tests.sh unit

# 运行集成测试
./scripts/run-tests.sh integration

# 运行快速测试（排除慢速测试）
./scripts/run-tests.sh quick

# 运行性能测试
./scripts/run-tests.sh performance

# 清理测试结果
./scripts/run-tests.sh clean

# 显示帮助信息
./scripts/run-tests.sh help
```

### 测试配置

#### Pytest 配置 (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "8.0"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
testpaths = ["tests"]

# 测试标记
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "requires_network: marks tests that require network access",
    "requires_browser: marks tests that require browser setup"
]

# 异步支持
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

# 日志配置
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
```

#### 覆盖率配置

```toml
[tool.coverage.run]
source = ["extractor"]
omit = [
    "extractor/__init__.py",
    "tests/*",
    "venv/*",
    ".venv/*"
]
branch = true
parallel = true

[tool.coverage.report]
show_missing = true
skip_covered = false
sort = "Cover"
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:"
]
```

### 命令行测试执行

#### 基础测试命令

```bash
# 运行所有测试
uv run pytest

# 运行特定目录的测试
uv run pytest tests/unit/
uv run pytest tests/integration/

# 运行特定文件的测试
uv run pytest tests/unit/test_config.py

# 运行特定测试类或方法
uv run pytest tests/unit/test_config.py::TestDataExtractorSettings
uv run pytest tests/unit/test_config.py::TestDataExtractorSettings::test_default_settings
```

#### 高级测试选项

```bash
# 详细输出模式
uv run pytest -v

# 并行测试（需要 pytest-xdist）
uv run pytest -n auto
uv run pytest -n 4

# 失败时停止
uv run pytest -x

# 重新运行失败的测试
uv run pytest --lf

# 显示最慢的测试
uv run pytest --durations=10

# 生成覆盖率报告
uv run pytest --cov=extractor --cov-report=html

# 生成 JUnit XML 报告
uv run pytest --junitxml=test-results.xml
```

#### 测试标记使用

```bash
# 运行单元测试
uv run pytest -m unit

# 运行集成测试
uv run pytest -m integration

# 排除慢速测试
uv run pytest -m "not slow"

# 运行需要网络的测试
uv run pytest -m requires_network

# 运行需要浏览器的测试
uv run pytest -m requires_browser
```

## 手动测试

### 测试环境准备

#### 1. 环境设置

```bash
# 安装开发依赖
uv sync --extra dev

# 设置环境变量
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
export DATA_EXTRACTOR_CONCURRENT_REQUESTS=1
```

#### 2. 测试数据准备

```python
# 使用测试夹具
@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Heading</h1>
        <div class="content">
            <p>Test paragraph 1</p>
            <p>Test paragraph 2</p>
        </div>
    </body>
    </html>
    """
```

### 调试测试

#### 1. 详细输出调试

```bash
# 显示详细输出和打印信息
uv run pytest -v -s

# 显示更短的错误信息
uv run pytest --tb=short

# 显示完整错误信息
uv run pytest --tb=long
```

#### 2. 交互式调试

```bash
# 使用 PDB 调试
uv run pytest --pdb

# 使用 IPython 调试器
uv run pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

#### 3. 内存和性能分析

```bash
# 内存使用分析（需要 pytest-monitor）
uv run pytest --monitor

# 性能基准测试
uv run pytest --benchmark-only
```

## 测试报告

### 报告类型

#### 1. HTML 报告

```bash
# 生成主测试报告
uv run pytest --html=tests/reports/test-report.html --self-contained-html

# 查看报告
open tests/reports/test-report.html  # macOS
xdg-open tests/reports/test-report.html  # Linux
```

#### 2. 覆盖率报告

```bash
# 生成 HTML 覆盖率报告
uv run pytest --cov=extractor --cov-report=html:htmlcov

# 查看覆盖率报告
open htmlcov/index.html

# 终端覆盖率显示
uv run coverage report --show-missing
```

#### 3. JSON 报告

```bash
# 生成 JSON 测试结果
uv run pytest --json-report --json-report-file=tests/reports/test-results.json

# 解析 JSON 报告
cat tests/reports/test-results.json | jq '.summary'
```

#### 4. XML 报告

```bash
# 生成 JUnit XML 报告
uv run pytest --junitxml=tests/reports/junit-results.xml

# 生成 Cobertura XML 覆盖率报告
uv run coverage xml -o tests/reports/coverage.xml
```

### 报告解读

#### 测试结果示例

```json
{
  "summary": {
    "total": 219,
    "passed": 216,
    "failed": 0,
    "skipped": 3,
    "duration": 47.92,
    "success_rate": "98.6%"
  },
  "tests": [
    {
      "name": "test_scrape_webpage_success",
      "status": "passed",
      "duration": 0.123,
      "module": "test_mcp_tools"
    }
  ]
}
```

#### 覆盖率指标

| 指标       | 当前值 | 目标值 | 说明             |
| ---------- | ------ | ------ | ---------------- |
| 总体覆盖率 | 98%    | >95%   | 整体代码覆盖率   |
| 行覆盖率   | 98%    | >95%   | 代码行覆盖情况   |
| 分支覆盖率 | 95%    | >90%   | 条件分支覆盖情况 |
| 函数覆盖率 | 100%   | >95%   | 函数定义覆盖情况 |

## 质量分析

### 代码质量指标

#### 测试覆盖分析

```python
# 覆盖率目标分解
coverage_targets = {
    "WebScraper": {"target": 95, "current": 97},
    "MarkdownConverter": {"target": 95, "current": 98},
    "PDFProcessor": {"target": 90, "current": 94},
    "MCP Tools": {"target": 95, "current": 98},
    "Utils": {"target": 95, "current": 99}
}
```

#### 性能基准

| 测试类型             | 基准时间 | 当前性能 | 状态    |
| -------------------- | -------- | -------- | ------- |
| 单元测试             | <30 秒   | ~15 秒   | ✅ 优秀 |
| 集成测试             | <2 分钟  | ~47 秒   | ✅ 优秀 |
| 完整测试套件         | <5 分钟  | ~3 分钟  | ✅ 优秀 |
| 并发测试 (20 个任务) | <30 秒   | ~25 秒   | ✅ 良好 |

### 测试质量保障

#### 1. 测试最佳实践

**命名规范**：

```python
def test_function_behavior_condition():
    """测试函数在特定条件下的行为"""
    pass

class TestClassName:
    """测试类名称规范"""

    def test_method_scenario(self):
        """测试方法场景"""
        pass
```

**测试结构**：

```python
def test_example():
    # Arrange - 准备测试数据
    test_data = {"key": "value"}

    # Act - 执行被测试的操作
    result = function_under_test(test_data)

    # Assert - 验证结果
    assert result["success"] is True
```

**异常测试**：

```python
def test_error_handling():
    """测试错误处理"""
    with pytest.raises(ValueError, match="Invalid input"):
        function_with_validation("invalid_input")
```

#### 2. Mock 策略

```python
from unittest.mock import Mock, AsyncMock, patch

def test_with_mock():
    # Mock 外部依赖
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    with patch('requests.get', return_value=mock_response):
        result = function_that_uses_requests()
        assert result is not None
```

#### 3. 参数化测试

```python
@pytest.mark.parametrize("input_url,expected", [
    ("https://example.com", True),
    ("http://test.org", True),
    ("not-a-url", False),
    ("", False),
])
def test_url_validation(input_url, expected):
    validator = URLValidator()
    assert validator.is_valid(input_url) == expected
```

## CI/CD 集成

### GitHub Actions 配置

#### 主 CI 工作流

```yaml
name: CI

on:
  push:
    branches: [master, main, develop]
  pull_request:
    branches: [master, main, develop]

jobs:
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest -v --tb=short
        env:
          DATA_EXTRACTOR_ENABLE_JAVASCRIPT: false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 质量门禁

#### 测试通过率要求

- **单元测试通过率**：>99%
- **集成测试通过率**：>95%
- **总体测试通过率**：>98%
- **代码覆盖率**：>95%

#### 性能要求

- **测试执行时间**：<5 分钟
- **内存使用**：<1GB
- **并发处理**：支持 20 个并发任务

## 故障排除

### 常见问题及解决方案

#### 1. 浏览器相关测试失败

**问题**：Selenium 或 Playwright 测试失败

```bash
# 解决方案：禁用浏览器测试
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
uv run pytest -k "not requires_browser"

# 或使用 headless 模式
export PLAYWRIGHT_BROWSERS_PATH=0
uv run playwright install --with-deps
```

#### 2. 网络相关测试失败

**问题**：网络连接超时或失败

```bash
# 解决方案：跳过网络依赖测试
uv run pytest -k "not requires_network"

# 或使用 Mock 模拟网络请求
pytest --mock-network
```

#### 3. 异步测试问题

**问题**：异步测试超时或失败

```bash
# 解决方案：增加超时时间
uv run pytest --asyncio-mode=auto --timeout=60

# 检查异步装饰器使用
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

#### 4. 内存不足问题

**问题**：测试过程中内存不足

```bash
# 解决方案：减少并发数量
uv run pytest -n 1

# 或清理测试数据
rm -rf /tmp/test_cache_*
```

### 调试技巧

#### 1. 日志调试

```python
import logging
logger = logging.getLogger(__name__)

def test_with_logging():
    logger.info("Starting test")
    # 测试逻辑
    logger.debug(f"Result: {result}")
```

#### 2. 断点调试

```python
def test_debug_example():
    import pdb; pdb.set_trace()  # 设置断点
    # 测试代码
    assert True
```

#### 3. 性能分析

```python
import time
import pytest

@pytest.mark.slow
def test_performance():
    start_time = time.time()
    result = expensive_operation()
    duration = time.time() - start_time

    assert duration < 5.0  # 确保执行时间在5秒内
```

## 测试数据管理

### 测试夹具 (Fixtures)

#### 核心夹具

```python
@pytest.fixture
def test_config():
    """安全的测试配置"""
    return DataExtractorSettings(
        server_name="Test Data Extractor",
        enable_javascript=False,
        concurrent_requests=1,
        browser_timeout=10,
        max_retries=2,
    )

@pytest.fixture
def mock_web_scraper():
    """模拟 WebScraper 实例"""
    scraper = Mock(spec=WebScraper)
    scraper.scrape_url = AsyncMock()
    return scraper

@pytest.fixture
def sample_html():
    """标准 HTML 测试内容"""
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>Test Content</p>
    </body>
    </html>
    """
```

### 测试数据文件

#### 外部测试数据

```
tests/
├── fixtures/
│   ├── html/
│   │   ├── simple_page.html
│   │   ├── complex_page.html
│   │   └── malformed.html
│   ├── pdf/
│   │   ├── sample.pdf
│   │   ├── large_document.pdf
│   │   └── encrypted.pdf
│   └── data/
│       ├── urls.json
│       ├── test_cases.json
│       └── expected_results.json
```

## 最佳实践

### 1. 测试设计原则

- **独立性**：每个测试应该独立运行，不依赖其他测试
- **可重复性**：测试结果应该是可重复的，不受环境影响
- **快速执行**：单元测试应该快速执行，集成测试可以稍慢
- **清晰断言**：使用明确的断言，提供清晰的错误信息

### 2. 测试组织

- **按功能分组**：将相关功能的测试组织在一起
- **使用标记**：合理使用 pytest 标记进行分类
- **命名规范**：使用清晰的测试命名规范
- **文档说明**：为复杂测试提供文档说明

### 3. 维护策略

- **定期更新**：定期检查和更新测试用例
- **覆盖率监控**：持续监控代码覆盖率
- **性能基准**：建立性能基准并定期检查
- **回归测试**：确保新功能不破坏现有功能

---

通过遵循本测试指南，团队可以建立和维护高质量的测试体系，确保 Data Extractor 项目的稳定性、可靠性和持续改进。
