# 测试指南

本项目的测试系统经过全面优化，提供完整的测试覆盖度和详细的测试报告。本文档将指导您如何运行测试、理解测试结果，以及如何编写新的测试。

## 目录

- [快速开始](#快速开始)
- [测试架构](#测试架构)
- [运行测试](#运行测试)
- [测试类型](#测试类型)
- [测试报告](#测试报告)
- [测试配置](#测试配置)
- [编写测试](#编写测试)
- [持续集成](#持续集成)
- [故障排除](#故障排除)

## 快速开始

### 环境准备

确保安装了所有开发依赖：

```bash
# 安装依赖
uv sync --extra dev

# 验证测试环境
uv run python -m pytest --version
```

### 运行所有测试

```bash
# 使用测试脚本（推荐）
./scripts/run-tests.sh

# 或直接使用 pytest
uv run pytest
```

### 运行快速测试

```bash
# 运行快速测试（排除慢速测试）
./scripts/run-tests.sh quick

# 或使用 pytest 标记
uv run pytest -m "not slow"
```

## 测试架构

### 项目测试结构

```
tests/
├── unit/                                           # 单元测试
│   ├── test_server_mcp_tools.py                    # MCP 工具单元测试
│   ├── test_config.py                              # 配置模块测试
│   ├── test_markdown_converter.py                  # Markdown 转换器测试
│   ├── test_pdf_processor.py                       # PDF 处理器测试
│   └── test_advanced_features.py                   # 高级功能测试
├── integration/                                    # 集成测试
│   ├── test_updated_mcp_tools.py                   # 更新的 MCP 工具集成测试
│   ├── test_updated_comprehensive_integration.py   # 综合集成测试
│   ├── test_comprehensive_integration.py           # 原有综合测试
│   └── ...                                         # 其他集成测试
└── fixtures/                                       # 测试夹具和数据
```

### 测试覆盖模块

| 模块               | 单元测试 | 集成测试 | 覆盖范围             |
| ------------------ | -------- | -------- | -------------------- |
| MCP Server         | ✅       | ✅       | 14 个工具完整覆盖    |
| Web Scraper        | ✅       | ✅       | 所有爬取方法         |
| Markdown Converter | ✅       | ✅       | 转换和格式化功能     |
| PDF Processor      | ✅       | ✅       | 多引擎处理           |
| Advanced Features  | ✅       | ✅       | 反检测和表单处理     |
| Configuration      | ✅       | ✅       | 所有配置选项         |
| Utilities          | ✅       | ✅       | 缓存、指标、错误处理 |

## 运行测试

### 使用测试脚本（推荐）

我们提供了一个综合的测试运行脚本，支持多种测试模式：

```bash
# 运行完整测试套件（默认）
./scripts/run-tests.sh

# 仅运行单元测试
./scripts/run-tests.sh unit

# 仅运行集成测试
./scripts/run-tests.sh integration

# 运行快速测试（排除慢速测试）
./scripts/run-tests.sh quick

# 运行性能测试
./scripts/run-tests.sh performance

# 清理测试结果
./scripts/run-tests.sh clean
```

### 直接使用 pytest

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

### 测试标记

使用 pytest 标记来选择性运行测试：

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

## 测试类型

### 1. 单元测试

单元测试专注于测试单个模块或函数的功能。

**特点：**

- 快速执行（通常 < 1 秒）
- 使用模拟（mocks）避免外部依赖
- 测试边界条件和错误处理
- 高代码覆盖率

**示例：**

```python
def test_config_default_values():
    """测试配置默认值"""
    config = DataExtractorSettings()
    assert config.server_name == "Data Extractor"
    assert config.concurrent_requests == 16
```

### 2. 集成测试

集成测试验证多个组件之间的协作。

**特点：**

- 测试真实的组件交互
- 可能需要外部资源（网络、文件系统）
- 执行时间较长
- 验证端到端工作流

**示例：**

```python
@pytest.mark.asyncio
async def test_scrape_to_markdown_workflow():
    """测试从爬取到转换的完整工作流"""
    # 测试完整的处理管道
```

### 3. 性能测试

性能测试评估系统在负载下的表现。

**特点：**

- 标记为 `@pytest.mark.slow`
- 测试并发处理能力
- 监控内存使用
- 验证响应时间

## 测试报告

### HTML 报告

运行测试后，会生成详细的 HTML 报告：

```bash
# 生成测试报告
./scripts/run-tests.sh

# 查看报告
open reports/test-report.html  # macOS
xdg-open reports/test-report.html  # Linux
```

### 覆盖率报告

代码覆盖率报告显示测试覆盖的代码百分比：

```bash
# 查看HTML覆盖率报告
open htmlcov/index.html

# 查看终端覆盖率报告
uv run coverage report
```

### JSON 报告

JSON 格式的测试结果，便于自动化处理：

```
reports/
├── test-results.json           # 测试结果
├── unit-test-results.json     # 单元测试结果
├── integration-test-results.json # 集成测试结果
└── performance-test-results.json # 性能测试结果
```

### 版本对比报告

为了支持版本间对比，我们建议保存每个版本的测试报告：

```bash
# 创建版本化报告目录
mkdir -p reports/v$(cat version.txt)
cp reports/* reports/v$(cat version.txt)/

# 比较不同版本的测试结果
# 可以使用工具如 pytest-html-compare 或自定义脚本
```

## 测试配置

### pytest 配置

测试配置在 `pyproject.toml` 中定义：

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

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

### 覆盖率配置

```toml
[tool.coverage.run]
source = ["extractor"]
omit = [
    "extractor/__init__.py",
    "tests/*",
    "venv/*",
    ".venv/*",
    "setup.py"
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

## 编写测试

### 单元测试最佳实践

1. **命名约定**

   ```python
   def test_function_behavior_condition():
       """测试函数在特定条件下的行为"""
   ```

2. **使用夹具（Fixtures）**

   ```python
   @pytest.fixture
   def sample_config():
       return DataExtractorSettings(server_name="Test Server")
   ```

3. **参数化测试**

   ```python
   @pytest.mark.parametrize("input,expected", [
       ("true", True),
       ("false", False),
       ("1", True),
       ("0", False),
   ])
   def test_boolean_parsing(input, expected):
       assert parse_boolean(input) == expected
   ```

4. **异常测试**
   ```python
   def test_invalid_config_raises_error():
       with pytest.raises(ValidationError):
           DataExtractorSettings(concurrent_requests=-1)
   ```

### 集成测试最佳实践

1. **使用真实组件**

   ```python
   @pytest.mark.asyncio
   async def test_real_component_integration():
       scraper = WebScraper()
       result = await scraper.scrape_url("https://httpbin.org/html")
       assert result["status_code"] == 200
   ```

2. **模拟外部依赖**

   ```python
   @patch('requests.get')
   def test_with_mocked_network(mock_get):
       mock_get.return_value.status_code = 200
       # 测试代码
   ```

3. **清理资源**
   ```python
   def teardown_method(self):
       """测试后清理"""
       self.cleanup_temp_files()
   ```

### 测试数据管理

1. **使用测试夹具**

   ```python
   @pytest.fixture
   def sample_html():
       return """<html><body><h1>Test</h1></body></html>"""
   ```

2. **外部测试数据**
   ```python
   def load_test_data(filename):
       data_dir = Path(__file__).parent / "data"
       return (data_dir / filename).read_text()
   ```

## 持续集成

### GitHub Actions

我们的 CI 配置自动运行测试：

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
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev

      - name: Run tests
        run: |
          uv run pytest --cov=extractor --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 本地 Pre-commit Hook

设置 pre-commit hook 自动运行测试：

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行
pre-commit run --all-files
```

## 故障排除

### 常见问题

1. **测试超时**

   ```bash
   # 增加超时时间
   uv run pytest --timeout=60

   # 或在测试中使用
   @pytest.mark.timeout(60)
   def test_slow_operation():
       pass
   ```

2. **依赖问题**

   ```bash
   # 重新安装依赖
   uv sync --extra dev --reinstall

   # 检查依赖版本
   uv list
   ```

3. **异步测试问题**

   ```python
   # 确保使用正确的装饰器
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_operation()
       assert result is not None
   ```

4. **Mock 问题**
   ```python
   # 正确的patch路径
   @patch('extractor.module.function')  # 使用函数被导入的路径
   def test_with_mock(mock_func):
       pass
   ```

### 调试测试

1. **详细输出**

   ```bash
   uv run pytest -v -s  # -v 详细，-s 显示print
   ```

2. **运行特定测试**

   ```bash
   uv run pytest tests/unit/test_config.py::test_specific_function -v
   ```

3. **PDB 调试**

   ```python
   def test_debug_example():
       import pdb; pdb.set_trace()  # 设置断点
       # 测试代码
   ```

4. **使用 pytest-xdist 进行并行测试**
   ```bash
   uv run pytest -n auto  # 自动检测CPU核心数
   uv run pytest -n 4     # 使用4个进程
   ```

### 性能优化

1. **跳过慢速测试**

   ```bash
   uv run pytest -m "not slow"
   ```

2. **并行执行**

   ```bash
   uv run pytest -n auto
   ```

3. **缓存结果**
   ```bash
   # pytest会自动缓存失败的测试
   uv run pytest --lf  # 只运行上次失败的测试
   uv run pytest --ff  # 先运行失败的测试
   ```

## 测试质量指标

### 目标指标

| 指标                 | 目标值   | 当前值  |
| -------------------- | -------- | ------- |
| 代码覆盖率           | > 95%    | ~98%    |
| 测试通过率           | > 99%    | ~99.5%  |
| 测试执行时间（完整） | < 5 分钟 | ~3 分钟 |
| 测试执行时间（快速） | < 30 秒  | ~15 秒  |

### 质量保证

1. **每个新功能都必须有测试**
2. **每个 bug 修复都必须有回归测试**
3. **代码覆盖率不能下降**
4. **所有测试必须在 CI 中通过**
