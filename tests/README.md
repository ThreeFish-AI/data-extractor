本指南说明如何运行和维护 Data Extractor 项目的测试套件。详细的测试用例说明和架构设计已迁移到对应的测试文件中。

## MCP 工具架构重构说明 (v0.1.5)

### 核心架构变更

**从 BaseModel 子类实现迁移到 Annotated Field 参数约束模式**

#### 重构前 (BaseModel 模式)

```python
# 定义请求模型
class ExtractLinksRequest(BaseModel):
    url: str
    filter_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    internal_only: bool = False

# MCP 工具函数
@app.tool()
async def extract_links(request: ExtractLinksRequest) -> LinksResponse:
    # 使用 request.url, request.filter_domains 等
```

#### 重构后 (Annotated Field 模式)

```python
# 直接参数定义，无需请求模型类
@app.tool()
async def extract_links(
    url: Annotated[str, Field(..., description="目标网页URL，必须包含协议前缀(http://或https://)")],
    filter_domains: Annotated[Optional[List[str]], Field(default=None, description="白名单域名列表，仅提取这些域名的链接")],
    exclude_domains: Annotated[Optional[List[str]], Field(default=None, description="黑名单域名列表，排除这些域名的链接")],
    internal_only: Annotated[bool, Field(default=False, description="是否仅提取内部链接(相同域名)")],
) -> LinksResponse:
    # 直接使用参数 url, filter_domains 等
```

#### 优势和改进

- **参数透明性**: 所有参数都明确可见，无需查看请求模型定义
- **描述清晰性**: 每个参数都有详细的中文描述和使用示例
- **MCP Client 兼容**: 增强的参数描述提升了 MCP Client 的自动化识别能力
- **减少样板代码**: 移除了大量 BaseModel 请求类定义，代码更简洁

## 测试架构概览

### 测试目录结构

```
tests/
├── __init__.py                     # 测试包初始化
├── conftest.py                     # Pytest 配置和共享 fixtures
├── unit/                           # 单元测试
│   ├── __init__.py
│   ├── test_scraper.py             # WebScraper 核心引擎测试 (含详细说明)
│   ├── test_advanced_features.py   # 高级功能测试 (反检测、表单处理) (含详细说明)
│   ├── test_utils.py               # 工具类测试 (限流、重试、缓存等) (含详细说明)
│   ├── test_markdown_converter.py  # MarkdownConverter 测试 (含详细说明)
│   └── test_pdf_processor.py       # PDFProcessor 测试
├── integration/                    # 集成测试
│   ├── __init__.py
│   ├── test_mcp_tools.py           # 14 个 MCP 工具集成测试 (含详细说明)
│   └── test_comprehensive_integration.py  # 综合集成测试 (端到端、性能、实际场景) (含详细说明)
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
@pytest.mark.parametrize("url,expected", [
    ("https://example.com", True),
    ("http://test.org", True),
    ("not-a-url", False),
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

---

**注意**: 具体的测试用例设计和详细说明已迁移到对应的测试文件中，实现了"工程代码即说明"的目标。请查看各测试文件顶部的详细文档字符串了解每个测试类和测试方法的具体功能和设计思路。
