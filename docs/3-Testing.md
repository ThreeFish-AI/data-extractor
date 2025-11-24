---
id: testing
sidebar_position: 3
title: Testing
description: 本文档提供 Data Extractor 项目的完整测试指南，涵盖测试架构、执行方法、质量保障和故障排除等全方位内容。
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - Testing
  - Quality Assurance
  - Test Coverage
  - CI/CD
---

## 🎯 测试体系概述

### 核心特点与架构原则

Data Extractor 项目建立了完整的测试体系，确保代码质量和系统稳定性：

- **高覆盖率**：整体测试覆盖率达 98%+
- **多层次测试**：单元测试 → 集成测试 → 端到端测试
- **自动化执行**：完整的 CI/CD 集成和自动化测试流程
- **详细报告**：HTML、JSON、XML 等多格式测试报告
- **性能监控**：内存使用、响应时间、并发性能监控

### 测试金字塔与标记体系

**测试类型分布**：

| 测试类型       | 占比 | 目标             | 特点                |
| -------------- | ---- | ---------------- | ------------------- |
| **单元测试**   | 70%  | 测试单个函数和类 | 快速执行、Mock 隔离 |
| **集成测试**   | 25%  | 测试模块间交互   | 真实组件交互        |
| **端到端测试** | 5%   | 测试完整业务流程 | 真实环境模拟        |

**测试标记分类**：

```python
@pytest.mark.unit           # 单元测试
@pytest.mark.integration    # 集成测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.requires_network   # 需要网络访问
@pytest.mark.requires_browser   # 需要浏览器环境
```

### 测试目录结构

```
tests/
├── conftest.py                     # Pytest 配置和共享 fixtures
├── unit/                           # 单元测试
│   ├── test_config.py              # 配置系统测试
│   ├── test_scraper.py             # 网页抓取引擎测试
│   ├── test_markdown_converter.py  # Markdown 转换器测试
│   ├── test_pdf_processor.py       # PDF 处理器测试
│   └── test_utils.py               # 工具类测试
├── integration/                    # 集成测试
│   ├── test_mcp_tools.py           # MCP 工具集成测试
│   ├── test_comprehensive_integration.py # 综合集成测试
│   └── test_end_to_end_integration.py # 端到端集成测试
└── reports/                        # 测试报告存储
    ├── test-report.html            # 主测试报告
    ├── htmlcov/                    # 覆盖率 HTML 报告
    └── *.json                      # 各类测试结果
```

### 模块覆盖概览

| 模块               | 单元测试 | 集成测试 | 覆盖范围             |
| ------------------ | -------- | -------- | -------------------- |
| MCP Server         | ✅       | ✅       | 14 个工具完整覆盖    |
| Web Scraper        | ✅       | ✅       | 所有爬取方法         |
| Markdown Converter | ✅       | ✅       | 转换和格式化功能     |
| PDF Processor      | ✅       | ✅       | 多引擎处理           |
| Configuration      | ✅       | ✅       | 所有配置选项         |
| Utilities          | ✅       | ✅       | 缓存、指标、错误处理 |

## 🏗️ 测试分类与实现

### 单元测试 (Unit Tests)

单元测试专注于测试独立模块和类的功能，具有快速执行、使用 Mock 隔离外部依赖、高代码覆盖率的特点。

**测试范围**：配置系统、网页抓取器、PDF 处理器、工具类等

**示例代码**：

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
        assert "url" in result and "data" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_extract_data_invalid_url(self):
        """测试无效URL"""
        extractor = DataExtractor(settings)
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await extractor.extract_data("")
```

### 集成测试 (Integration Tests)

集成测试验证多个组件之间的协作，使用真实组件交互、端到端工作流验证，专注于组件间的数据流和接口。

**测试范围**：MCP 工具集成、跨工具协作、真实场景模拟

**示例代码**：

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

**集成测试最佳实践**：

- **使用真实组件**：优先使用真实组件进行测试
- **模拟外部依赖**：对外部不可控依赖使用 Mock
- **资源清理**：确保测试后清理临时资源和状态
- **环境隔离**：使用独立的测试环境避免交叉影响

### 性能测试与端到端测试

**性能测试 (Performance Tests)**：

- **目标**：评估系统在负载下的表现
- **内容**：并发处理测试、内存使用监控、响应时间验证
- **范围**：批量处理、大文档处理、长期稳定性

**端到端测试 (E2E Tests)**：

- **目标**：验证完整的业务流程
- **内容**：真实环境模拟、完整工作流测试
- **范围**：文档处理管道、错误恢复、数据一致性

## 🚀 测试执行与配置

### 快速开始指南

**使用测试脚本**：项目提供了综合的测试运行脚本 `scripts/run-tests.sh`：

```bash
# 运行完整测试套件（默认）
./scripts/run-tests.sh

# 按类型运行测试
./scripts/run-tests.sh unit           # 单元测试
./scripts/run-tests.sh integration    # 集成测试
./scripts/run-tests.sh quick          # 快速测试（排除慢速测试）
./scripts/run-tests.sh performance    # 性能测试
./scripts/run-tests.sh clean          # 清理测试结果
./scripts/run-tests.sh help           # 显示帮助信息
```

**基础 pytest 命令**：

```bash
# 运行不同范围的测试
uv run pytest                              # 所有测试
uv run pytest tests/unit/                  # 单元测试目录
uv run pytest tests/integration/           # 集成测试目录
uv run pytest tests/unit/test_config.py    # 特定文件

# 运行特定测试类或方法
uv run pytest tests/unit/test_config.py::TestDataExtractorSettings
uv run pytest tests/unit/test_config.py::TestDataExtractorSettings::test_default_settings
```

### 高级测试选项与配置

**测试执行控制**：

```bash
# 输出控制
uv run pytest -v                           # 详细输出
uv run pytest -s                           # 显示 print 信息
uv run pytest --tb=short                   # 简短错误信息
uv run pytest --tb=long                    # 详细错误信息

# 测试选择与执行
uv run pytest -x                           # 首次失败时停止
uv run pytest --lf                         # 只运行上次失败的测试
uv run pytest --ff                         # 先运行失败的测试
uv run pytest --durations=10               # 显示最慢的10个测试

# 并行执行
uv run pytest -n auto                      # 自动并行
uv run pytest -n 4                         # 4个进程并行

# 按标记运行
uv run pytest -m unit                      # 单元测试
uv run pytest -m integration               # 集成测试
uv run pytest -m "not slow"                # 排除慢速测试
uv run pytest -m requires_network          # 需要网络的测试
uv run pytest -m requires_browser          # 需要浏览器的测试
```

**报告生成**：

```bash
# HTML 报告
uv run pytest --html=tests/reports/test-report.html --self-contained-html

# 覆盖率报告
uv run pytest --cov=extractor --cov-report=html:tests/reports/htmlcov
uv run pytest --cov=extractor --cov-report=term-missing

# XML 报告（CI/CD 集成）
uv run pytest --junitxml=tests/reports/junit-results.xml
uv run coverage xml -o tests/reports/coverage.xml

# JSON 报告
uv run pytest --json-report --json-report-file=tests/reports/test-results.json
```

**Pytest 配置 (pyproject.toml)**：

```toml
[tool.pytest.ini_options]
minversion = "8.0"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
testpaths = ["tests"]

# 测试标记定义
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

**覆盖率配置**：

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

## 🔧 测试环境与调试

### 环境准备与配置

**环境设置**：

```bash
# 安装开发依赖
uv sync --extra dev

# 设置测试环境变量
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
export DATA_EXTRACTOR_CONCURRENT_REQUESTS=1
export DATA_EXTRACTOR_BROWSER_TIMEOUT=10
```

**测试数据准备**：

```python
# 使用测试夹具准备测试数据
@pytest.fixture
def sample_html():
    """标准 HTML 测试内容"""
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

### 调试方法与工具

**输出调试**：

```bash
# 显示详细输出和打印信息
uv run pytest -v -s

# 控制错误信息显示
uv run pytest --tb=short    # 简短错误信息
uv run pytest --tb=long     # 详细错误信息
uv run pytest --tb=no       # 不显示错误信息
```

**交互式调试**：

```bash
# 使用 PDB 调试器
uv run pytest --pdb

# 使用 IPython 调试器
uv run pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb

# 在特定测试处设置断点
def test_debug_example():
    import pdb; pdb.set_trace()  # 设置断点
    assert True
```

**性能与内存分析**：

```bash
# 内存使用分析
uv run pytest --monitor

# 性能基准测试
uv run pytest --benchmark-only

# 显示测试执行时间
uv run pytest --durations=0
```

### 测试夹具与数据管理

**核心夹具示例**：

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
async def sample_response():
    """模拟 HTTP 响应"""
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = "<html><body>Test</body></html>"

        async def json(self):
            return {"data": "test"}

    return MockResponse()
```

**测试数据管理**：

```python
# 外部测试数据加载
def load_test_data(filename):
    """加载外部测试数据文件"""
    data_dir = Path(__file__).parent / "fixtures" / "data"
    return (data_dir / filename).read_text()

# 使用参数化测试
@pytest.mark.parametrize("url,expected_status", [
    ("https://httpbin.org/html", 200),
    ("https://httpbin.org/json", 200),
])
async def test_url_status(url, expected_status):
    """参数化测试示例"""
    response = await fetch_url(url)
    assert response.status_code == expected_status
```

## 📊 测试报告与质量分析

### 报告生成与质量指标

**HTML 报告**：

```bash
# 生成主测试报告
uv run pytest --html=tests/reports/test-report.html --self-contained-html

# 查看报告（根据操作系统选择）
open tests/reports/test-report.html          # macOS
xdg-open tests/reports/test-report.html      # Linux
start tests/reports/test-report.html         # Windows
```

**覆盖率报告**：

```bash
# 生成 HTML 覆盖率报告
uv run pytest --cov=extractor --cov-report=html:tests/reports/htmlcov

# 查看覆盖率报告
open tests/reports/htmlcov/index.html

# 终端覆盖率显示
uv run coverage report --show-missing
```

**多格式报告**：

```bash
# JSON 报告（便于 CI/CD 集成）
uv run pytest --json-report --json-report-file=tests/reports/test-results.json

# JUnit XML 报告（CI/CD 标准）
uv run pytest --junitxml=tests/reports/junit-results.xml

# Cobertura XML 覆盖率报告
uv run coverage xml -o tests/reports/coverage.xml

# 版本对比报告
mkdir -p reports/v$(cat version.txt 2>/dev/null || echo "latest")
cp reports/*.{html,json,xml} reports/v$(cat version.txt 2>/dev/null || echo "latest")/
```

**质量指标示例**：

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
  "coverage": {
    "total": "98%",
    "lines": "98%",
    "branches": "95%",
    "functions": "100%"
  }
}
```

## 🏆 测试质量保障与最佳实践

### 测试设计原则

**核心原则**：

- **独立性**：每个测试应该独立运行，不依赖其他测试
- **可重复性**：测试结果应该是可重复的，不受环境影响
- **快速执行**：单元测试应该快速执行，集成测试可以稍慢
- **清晰断言**：使用明确的断言，提供清晰的错误信息

**命名规范与结构**：

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

**AAA 测试模式**：

```python
def test_example():
    # Arrange - 准备测试数据
    test_data = {"key": "value"}

    # Act - 执行被测试的操作
    result = function_under_test(test_data)

    # Assert - 验证结果
    assert result["success"] is True
```

**异常测试模式**：

```python
def test_error_handling():
    """测试错误处理"""
    with pytest.raises(ValueError, match="Invalid input"):
        function_with_validation("invalid_input")
```

### 高级测试技巧与策略

**Mock 与 Patch 策略**：

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

# 异步 Mock
@pytest.mark.asyncio
async def test_async_mock():
    mock_async_func = AsyncMock(return_value={"result": "success"})
    result = await mock_async_func()
    assert result["result"] == "success"
```

**参数化测试**：

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

# 复杂参数化测试
@pytest.mark.parametrize("method,status_code,expected", [
    ("GET", 200, "success"),
    ("POST", 201, "created"),
    ("DELETE", 204, "no_content"),
])
async def test_http_responses(method, status_code, expected):
    response = await make_request(method, "/test")
    assert response.status_code == status_code
    assert response.message == expected
```

**测试数据管理**：

```python
# 使用 fixtures 管理测试数据
@pytest.fixture(params=["simple", "complex", "edge_case"])
def test_scenario(request):
    """参数化夹具"""
    scenarios = {
        "simple": {"url": "https://example.com", "expected": "success"},
        "complex": {"url": "https://complex-site.com", "expected": "partial"},
        "edge_case": {"url": "", "expected": "error"}
    }
    return scenarios[request.param]

# 外部数据文件管理
def load_test_cases():
    """从 JSON 文件加载测试用例"""
    with open("tests/fixtures/test_cases.json") as f:
        return json.load(f)
```

## 🔄 CI/CD 集成与自动化

### GitHub Actions 基础 CI 配置

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
        run: uv run pytest -v --tb=short --cov=extractor
        env:
          DATA_EXTRACTOR_ENABLE_JAVASCRIPT: false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 高级 CI/CD 工作流

```yaml
name: Advanced CI/CD

on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  test-matrix:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.12", "3.13"]
        test-type: [unit, integration, performance]

    steps:
      - uses: actions/checkout@v4
      - name: Setup Environment
        run: |
          uv sync --extra dev
          echo "DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false" >> $GITHUB_ENV

      - name: Run ${{ matrix.test-type }} tests
        run: |
          if [ "${{ matrix.test-type }}" = "unit" ]; then
            uv run pytest -m unit --cov=extractor
          elif [ "${{ matrix.test-type }}" = "integration" ]; then
            uv run pytest -m integration -v
          elif [ "${{ matrix.test-type }}" = "performance" ]; then
            uv run pytest -m performance --benchmark-only
          fi

  quality-gate:
    needs: test-matrix
    runs-on: ubuntu-latest
    steps:
      - name: Quality Gate Check
        run: |
          # 检查覆盖率、性能等质量指标
          python scripts/check_quality_gate.py
```

### 本地 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run tests
        entry: uv run pytest -m "not slow"
        language: system
        pass_filenames: false
        always_run: true

      - id: check-coverage
        name: Check coverage
        entry: uv run pytest --cov=extractor --cov-fail-under=95
        language: system
        pass_filenames: false

      - id: lint-code
        name: Lint code
        entry: uv run ruff check .
        language: system
        always_run: true
```

```bash
# 安装和使用 pre-commit
pip install pre-commit
pre-commit install
pre-commit run --all-files  # 手动运行
```

### 质量门禁标准

| 指标           | 要求    | 当前状态 | 通过情况 |
| -------------- | ------- | -------- | -------- |
| 单元测试通过率 | >99%    | 99.2%    | ✅       |
| 集成测试通过率 | >95%    | 98.6%    | ✅       |
| 总体测试通过率 | >98%    | 98.6%    | ✅       |
| 代码覆盖率     | >95%    | 98%      | ✅       |
| 测试执行时间   | <5 分钟 | ~3 分钟  | ✅       |
| 内存使用       | <1GB    | ~512MB   | ✅       |
| 并发处理能力   | 20 任务 | 通过     | ✅       |

## 🚨 故障排除与维护

### 常见问题与解决方案

**浏览器相关问题**：

```bash
# Selenium 或 Playwright 测试失败解决方案
# 方案1：禁用浏览器测试
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=false
uv run pytest -k "not requires_browser"

# 方案2：使用 headless 模式
export PLAYWRIGHT_BROWSERS_PATH=0
uv run playwright install --with-deps
uv run pytest --browser chromium --headless
```

**网络连接问题**：

```bash
# 网络超时或连接失败解决方案
# 跳过网络依赖测试
uv run pytest -k "not requires_network"

# 使用 Mock 模拟网络请求
uv run pytest --mock-network

# 增加超时设置
uv run pytest --timeout=30
```

**异步测试问题**：

```bash
# 异步测试超时或失败解决方案
# 增加异步超时时间
uv run pytest --asyncio-mode=auto --timeout=60

# 检查异步装饰器使用
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

**性能与资源问题**：

```bash
# 内存不足或执行缓慢解决方案
# 减少并发数量
uv run pytest -n 1

# 清理测试缓存
rm -rf /tmp/test_cache_*
rm -rf .pytest_cache/

# 跳过慢速测试
uv run pytest -m "not slow"
```

### 调试与性能分析

**日志调试**：

```python
import logging
logger = logging.getLogger(__name__)

def test_with_logging():
    logger.info("Starting test")
    result = some_operation()
    logger.debug(f"Result: {result}")
    assert result is not None
```

**断点调试**：

```python
def test_debug_example():
    import pdb; pdb.set_trace()  # 设置断点
    # 测试代码
    assert True

# 使用 IPython 调试器
uv run pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

**性能分析**：

```python
import time
import pytest

@pytest.mark.slow
def test_performance_benchmark():
    start_time = time.time()
    result = expensive_operation()
    duration = time.time() - start_time

    assert duration < 5.0  # 确保执行时间在5秒内
    assert result is not None
```

### 测试数据与维护策略

**测试数据结构**：

```
tests/
├── fixtures/
│   ├── html/           # HTML 测试文件
│   ├── pdf/            # PDF 测试文件
│   └── data/           # JSON 测试数据
└── conftest.py         # 共享夹具
```

**测试数据管理**：

```python
# 使用夹具管理
@pytest.fixture
def sample_html():
    """标准 HTML 测试内容"""
    return """<html><body><h1>Test</h1></body></html>"""

@pytest.fixture(params=["simple", "complex"])
def test_scenarios(request):
    """参数化测试场景"""
    return load_scenario(request.param)

# 外部数据加载
def load_test_data(filename):
    """加载外部测试数据文件"""
    data_dir = Path(__file__).parent / "fixtures" / "data"
    return (data_dir / filename).read_text()
```

**维护与优化策略**：

**定期维护任务**：

- **测试用例更新**：定期检查和更新过时的测试用例
- **覆盖率监控**：持续监控代码覆盖率，确保不下降
- **性能基准检查**：建立性能基准并定期检查回归
- **依赖更新**：定期更新测试依赖和工具

**测试组织最佳实践**：

- **功能分组**：按功能模块组织测试文件
- **标记分类**：合理使用 pytest 标记进行测试分类
- **命名规范**：使用清晰、一致的测试命名规范
- **文档说明**：为复杂测试提供充分的文档说明

**持续改进**：

- **测试反馈**：收集和分析测试失败反馈
- **自动化增强**：逐步提高测试自动化程度
- **工具优化**：定期评估和优化测试工具链
- **团队培训**：定期进行测试最佳实践培训

---

通过遵循本测试指南，团队可以建立和维护高质量的测试体系，确保 Data Extractor 项目的稳定性、可靠性和持续改进。
