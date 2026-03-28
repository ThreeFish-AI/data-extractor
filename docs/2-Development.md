---
id: development
sidebar_position: 2
title: Development
description: Development Guide and Best Practices
last_update:
  author: Aurelius
  date: 2026-03-22
tags:
  - Development
  - Guide
  - Best Practices
  - Workflow
---

Negentropy Perceives 采用现代化的 Python 开发工具链，基于 uv 包管理器构建高效的开发环境。本文档提供开发环境配置、项目结构总览、MCP 工具开发规范与编码最佳实践。

## 环境配置

### 系统要求

- **Python**: 3.13+
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最少 4GB RAM
- **存储**: 最少 10GB 可用空间

### 快速开始

```bash
# 使用提供的脚本快速设置（推荐）
./scripts/dev/setup.sh

# 验证环境设置
uv --version
python --version
```

### 详细环境配置

```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd negentropy-perceives

# 同步依赖
uv sync

# 安装开发依赖
uv sync --group dev

# 设置环境变量
cp .env.example .env

# 安装 Playwright 浏览器依赖
uv run playwright install chromium
```

## 项目结构

```
negentropy-perceives/
├── src/negentropy/perceives/                    # 核心包
│   ├── server.py                 # MCP 服务器入口（re-export + main()）
│   ├── config.py                 # 配置系统 + 配置验证（NegentropyPerceivesSettings, ConfigValidator）
│   ├── schemas.py                # 响应模型 + 数据传输对象（Pydantic BaseModel, ScrapingResult）
│   │
│   ├── scraper.py                # 网页抓取引擎（WebScraper）
│   ├── anti_detection.py         # 反检测隐身抓取（AntiDetectionScraper）
│   ├── browser_utils.py          # 浏览器工具
│   ├── form_handler.py           # 表单处理
│   │
│   ├── cache.py                  # 缓存管理
│   ├── rate_limiter.py           # 速率限制
│   ├── retry.py                  # 重试机制
│   ├── error_handler.py          # 错误处理
│   ├── metrics.py                # 指标收集
│   ├── timing.py                 # 计时装饰器
│   │
│   ├── url_utils.py              # URL 验证工具
│   ├── text_utils.py             # 文本清理工具
│   │
│   ├── pdf_processor.py          # PDF 处理器入口（兼容层）
│   ├── enhanced_pdf_processor.py # 增强 PDF（兼容层）
│   │
│   ├── tools/                    # MCP 工具注册子包
│   │   ├── _registry.py          # app 实例 + 共享服务 + 辅助函数
│   │   ├── scraping.py           # 网页抓取工具（6 个 tool）
│   │   ├── pdf.py                # PDF 处理工具（2 个 tool）
│   │   ├── markdown.py           # Markdown 转换工具（2 个 tool）
│   │   ├── form.py               # 表单工具（1 个 tool）
│   │   ├── utility.py            # 实用工具（1 个 tool）
│   │   └── service.py            # 服务管理工具（2 个 tool）
│   │
│   ├── pdf/                      # PDF 处理引擎子包
│   │   ├── processor.py          # 核心 PDF 处理器
│   │   └── enhanced.py           # 增强 PDF 处理器（PyMuPDF）
│   │
│   └── examples/                 # 示例与配置模板（随包分发）
│       ├── configs/
│       │   └── extraction_configs.py  # 领域提取配置模板
│       ├── mcp/
│       │   └── basic_usage.py         # MCP 工具调用示例
│       └── sdk/
│           └── python_sdk_usage.py    # Python SDK 集成示例
│
├── tests/                        # 测试套件
│   ├── conftest.py               # 共享 Fixtures
│   ├── unit/                     # 单元测试（16 个文件）
│   └── integration/              # 集成测试（9 个文件）
│
├── scripts/                      # 仓库维护脚本
│   ├── dev/
│   │   └── setup.sh              # 环境初始化
│   └── test/
│       └── run-tests.sh          # 测试执行（支持 unit/integration/full/coverage 等模式）
│
├── docs/                         # 项目文档
├── .github/workflows/            # CI/CD 配置
└── pyproject.toml                # 项目配置
```

## MCP 工具开发

### 分包注册架构

项目采用**分包注册模式**组织 MCP 工具，核心链路如下：

```
tools/_registry.py          定义 FastMCP app 实例 + 共享服务
       ↓
tools/scraping.py 等        用 @app.tool() 装饰器注册工具函数
       ↓
tools/__init__.py           导入各子模块，触发装饰器注册
       ↓
server.py                   re-export 所有工具（向后兼容）
```

`_registry.py` 是中枢，提供 `app` 实例和共享服务（`web_scraper`、`anti_detection_scraper`、`markdown_converter`）以及通用辅助函数（`validate_url`、`record_error`、`elapsed_ms` 等）。

### 开发新工具步骤

以 `check_robots_txt`（[tools/utility.py](../src/negentropy/perceives/tools/utility.py)）为例，这是项目中最简单的 MCP 工具：

#### 1. 定义响应模型

在 [schemas.py](../src/negentropy/perceives/schemas.py) 中添加 Pydantic 响应模型：

```python
class RobotsResponse(BaseModel):
    """Response model for robots.txt check."""
    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="检查的URL")
    robots_txt_url: str = Field(..., description="robots.txt文件URL")
    robots_content: Optional[str] = Field(default=None, description="robots.txt内容")
    is_allowed: bool = Field(..., description="是否允许抓取")
    user_agent: str = Field(..., description="使用的User-Agent")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")
```

#### 2. 实现工具函数

在 `tools/` 下对应模块中实现，通过 `@app.tool()` 注册：

```python
from ..schemas import RobotsResponse
from ._registry import app, web_scraper

@app.tool()
async def check_robots_txt(url: str) -> RobotsResponse:
    """Check the robots.txt file for a domain to understand crawling permissions."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        result = await web_scraper.simple_scraper.scrape(robots_url, extract_config={})

        if "error" in result:
            return RobotsResponse(success=False, url=url, robots_txt_url=robots_url,
                                  is_allowed=False, user_agent="*",
                                  error=f"Could not fetch robots.txt: {result['error']}")

        robots_content = result.get("content", {}).get("text", "")
        return RobotsResponse(success=True, url=url, robots_txt_url=robots_url,
                              robots_content=robots_content, is_allowed=True, user_agent="*")
    except Exception as e:
        return RobotsResponse(success=False, url=url, robots_txt_url="",
                              is_allowed=False, user_agent="*", error=str(e))
```

#### 3. 注册触发

在 [tools/\_\_init\_\_.py](../src/negentropy/perceives/tools/__init__.py) 中导入新模块：

```python
from . import utility  # noqa: F401  # 触发 @app.tool() 注册
```

如需向后兼容，还需在 [server.py](../src/negentropy/perceives/server.py) 中 re-export。

### 参数设计模式

推荐使用 **Annotated Field 模式**，直接在函数签名中定义参数描述，无需额外的请求模型类。以 [tools/scraping.py](../src/negentropy/perceives/tools/scraping.py) 中的 `scrape_webpage` 为例：

```python
@app.tool()
async def scrape_webpage(
    url: Annotated[str, Field(..., description="目标网页 URL，必须包含协议前缀（http://或https://）")],
    method: Annotated[str, Field(default="auto", description="抓取方法：auto/simple/scrapy/selenium")],
    extract_config: Annotated[Optional[Dict[str, Any]], Field(default=None, description="数据提取配置字典")],
    wait_for_element: Annotated[Optional[str], Field(default=None, description="等待元素的 CSS 选择器")],
) -> ScrapeResponse:
```

**优势**：参数透明可见、描述清晰、MCP Client 兼容性好、减少样板代码。

### 开发最佳实践

- **错误处理**：验证输入参数，使用 `_registry.py` 中的 `validate_url()` 和 `record_error()` 辅助函数，返回结构化错误信息
- **性能优化**：使用异步编程（`async/await`），利用 `cache.py` 缓存、`rate_limiter.py` 限速、`timing.py` 计时装饰器
- **架构参考**：系统性能设计详见 [架构设计](./1-Framework.md)

## 编码规范

遵循 PEP 8 和 PEP 257 标准。代码质量工具（Ruff、MyPy、Pre-commit）的使用详见 [常用指令](./5-Commands.md)。

### 类型注解与文档字符串

所有函数和方法应有类型注解和 Google 风格的文档字符串：

```python
from typing import Dict, List, Optional, Any

async def scrape_webpage(
    url: str,
    method: str = "auto",
    extract_config: Optional[Dict[str, Any]] = None,
) -> ScrapeResponse:
    """抓取网页数据

    Args:
        url: 要抓取的URL
        method: 抓取方法 (auto/simple/scrapy/selenium)
        extract_config: 数据提取配置

    Returns:
        抓取响应对象

    Raises:
        ValueError: URL格式错误
    """
    pass
```

## CI/CD 与版本管理

详见 [GitHub Actions 工作流](./2.1-Workflows.md) 和 [构建与发布流程](./5-Commands.md#构建与发布流程)。

## 调试与故障排除

### 日志调试

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractorService:
    async def extract_data(self, url: str):
        logger.info(f"Starting extraction for URL: {url}")
        # ...
        logger.info("Extraction completed successfully")
```

### 异步调试

```python
import asyncio

async def debug_async_function():
    """调试异步函数"""
    try:
        result = await some_async_operation()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        raise

asyncio.run(debug_async_function())
```

### 浏览器调试

```python
@pytest.mark.requires_browser
async def test_with_browser_debugging():
    """启用浏览器调试的测试"""
    from negentropy.perceives.scraping import AntiDetectionScraper

    scraper = AntiDetectionScraper()
    options = {
        "headless": False,
        "devtools": True,
        "slow_mo": 1000  # 慢速执行
    }
    # ...
```

### 常见问题解决

#### 浏览器驱动问题

```bash
# 重新安装 Playwright
uv run playwright install --force

# 或使用系统浏览器
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

#### 测试超时问题

```bash
# 增加超时时间或跳过慢速测试
uv run pytest -m "not slow" --timeout=300
```

#### 类型检查错误

```bash
# 逐步修复类型问题
uv run mypy src/negentropy/perceives/ --ignore-missing-imports

# 或使用宽松模式
uv run mypy src/negentropy/perceives/ --disable-error-code=var-annotated
```

更多调试命令详见 [常用指令](./5-Commands.md)，测试故障排除详见 [测试指南](./3-Testing.md#故障排除)。

## 开发资源

### 技术文档

- [uv 官方文档](https://docs.astral.sh/uv/)
- [pytest 文档](https://docs.pytest.org/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [MyPy 文档](https://mypy.readthedocs.io/)

### 工具推荐

- **IDE**: PyCharm, VS Code
- **API 测试**: Postman, Insomnia

## 相关文档

| 文档 | 说明 |
|------|------|
| [架构设计](./1-Framework.md) | 系统架构、设计模式、性能策略 |
| [CI/CD 工作流](./2.1-Workflows.md) | GitHub Actions、发布流程 |
| [测试指南](./3-Testing.md) | 测试架构、执行方法、质量保障 |
| [配置系统](./4-Configuration.md) | 环境变量、配置模板 |
| [常用指令](./5-Commands.md) | 命令速查手册 |
| [用户指南](./6-User-Guide.md) | 完整使用指南、API 参考 |
