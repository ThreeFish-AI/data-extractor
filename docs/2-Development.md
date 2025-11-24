---
id: development
sidebar_position: 2
title: Development
description: Development Guide and Best Practices
last_update:
  author: Aurelius
  date: 2025-11-23
tags:
  - Development
  - Guide
  - Best Practices
  - Workflow
---

Data Extractor 采用现代化的 Python 开发工具链，基于 uv 包管理器构建高效的开发环境。本文档提供完整的开发指南、最佳实践和代码质量保障机制。

## 环境配置

### 系统要求

- **Python**: 3.12+ （推荐 3.13）
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最少 4GB RAM
- **存储**: 最少 10GB 可用空间

### 快速开始

```bash
# 使用提供的脚本快速设置（推荐）
./scripts/setup.sh

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
cd data-extractor

# 同步依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 设置环境变量
cp .env.example .env

# 安装 Playwright 浏览器依赖
uv run playwright install chromium
```

## 项目结构

```
data-extractor/
├── extractor/                 # 核心模块
│   ├── __init__.py
│   ├── server.py              # MCP 服务器
│   ├── scraper.py             # 网页抓取引擎
│   ├── advanced_features.py   # 高级功能
│   ├── pdf_processor.py        # PDF 处理
│   ├── markdown_converter.py   # Markdown 转换
│   ├── config.py              # 配置系统
│   └── utils.py                # 工具函数
├── tests/                     # 测试套件
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── reports/               # 测试报告
├── scripts/                   # 开发脚本
│   ├── setup.sh              # 环境设置
│   ├── run-tests.sh           # 测试执行
│   └── update_version.py      # 版本更新
├── docs/                      # 文档
├── examples/                  # 示例代码
├── .github/workflows/         # CI/CD 配置
└── pyproject.toml            # 项目配置
```

## MCP 工具开发

### 快速开发示例

以下示例展示了如何快速开发一个完整的 MCP Tool，以创建一个简单的"网页标题提取器"为例：

#### 1. 定义请求和响应模型

```python
# 在 extractor/server.py 顶部添加响应模型
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TitleExtractionResponse(BaseModel):
    """标题提取响应模型"""
    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    title: Optional[str] = Field(default=None, description="提取的页面标题")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")
    timestamp: datetime = Field(default_factory=datetime.now, description="提取时间戳")
```

#### 2. 实现 MCP Tool 函数

```python
@app.tool()
async def extract_page_title(
    url: Annotated[
        str,
        Field(
            ...,
            description="目标网页 URL，必须包含协议前缀（http://或https://），将提取此页面的标题"
        ),
    ],
) -> TitleExtractionResponse:
    """
    提取网页标题

    这是一个简单的工具，用于快速获取网页的标题信息，常用于：
    - 网页内容分析前的预检查
    - 批量网页处理时的标题收集
    - 链接有效性验证

    Args:
        url: 目标网页 URL

    Returns:
        TitleExtractionResponse: 包含提取结果和元信息的响应对象
    """
    try:
        # 验证 URL 格式
        if not URLValidator.is_valid_url(url):
            return TitleExtractionResponse(
                success=False,
                url=url,
                error="Invalid URL format"
            )

        # 使用现有的网页抓取器获取页面信息
        page_info = await web_scraper.get_page_info(url)

        if not page_info.get("success", False):
            return TitleExtractionResponse(
                success=False,
                url=url,
                error=page_info.get("error", "Failed to fetch page")
            )

        # 提取标题
        title = page_info.get("data", {}).get("title", "No title found")

        return TitleExtractionResponse(
            success=True,
            url=url,
            title=title
        )

    except Exception as e:
        logger.error(f"Error extracting title from {url}: {str(e)}")
        return TitleExtractionResponse(
            success=False,
            url=url,
            error=f"Extraction failed: {str(e)}"
        )
```

#### 3. 添加单元测试

```python
# 在 tests/unit/ 目录下创建 test_title_extractor.py
import pytest
from unittest.mock import AsyncMock, patch
from extractor.server import extract_page_title, TitleExtractionResponse

@pytest.mark.asyncio
async def test_extract_page_title_success():
    """测试成功提取标题"""
    # 模拟网页抓取器返回
    mock_page_info = {
        "success": True,
        "data": {"title": "Example Page Title"}
    }

    with patch('extractor.server.web_scraper.get_page_info', new_callable=AsyncMock) as mock_scraper:
        mock_scraper.return_value = mock_page_info

        result = await extract_page_title("https://example.com")

        assert result.success is True
        assert result.title == "Example Page Title"
        assert result.url == "https://example.com"
        assert result.error is None

@pytest.mark.asyncio
async def test_extract_page_title_invalid_url():
    """测试无效 URL"""
    result = await extract_page_title("invalid-url")

    assert result.success is False
    assert "Invalid URL format" in result.error
    assert result.title is None

@pytest.mark.asyncio
async def test_extract_page_title_scraping_failure():
    """测试抓取失败"""
    mock_page_info = {
        "success": False,
        "error": "Connection timeout"
    }

    with patch('extractor.server.web_scraper.get_page_info', new_callable=AsyncMock) as mock_scraper:
        mock_scraper.return_value = mock_page_info

        result = await extract_page_title("https://example.com")

        assert result.success is False
        assert "Connection timeout" in result.error
```

#### 4. 测试新工具

```bash
# 运行特定测试
uv run pytest tests/unit/test_title_extractor.py -v

# 运行所有测试确保没有破坏现有功能
uv run pytest

# 启动开发服务器测试新工具
uv run python -m extractor.server
```

### 开发最佳实践

#### 参数设计模式

**Annotated Field 模式（推荐）**

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

**优势和改进**

- **参数透明性**: 所有参数都明确可见，无需查看请求模型定义
- **描述清晰性**: 每个参数都有详细的中文描述和使用示例
- **MCP Client 兼容**: 增强的参数描述提升了 MCP Client 的自动化识别能力
- **减少样板代码**: 移除了大量 BaseModel 请求类定义，代码更简洁

#### 错误处理策略

- 验证输入参数
- 捕获并记录异常
- 返回结构化的错误信息
- 使用现有的工具类（URLValidator、ErrorHandler）

#### 性能优化考虑

- 使用异步编程
- 利用缓存机制
- 添加适当的装饰器（如 `@timing_decorator`）
- 控制并发访问

## 代码质量保障

### 代码质量工具

**Ruff**：代码检查和格式化

```bash
# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .

# 导入排序
uv run ruff check --select I .
```

**MyPy**：类型检查

```bash
# 类型检查
uv run mypy extractor/

# 严格类型检查
uv run mypy --strict extractor/
```

**Pre-commit**：Git 钩子

```bash
# 安装钩子
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files
```

### Python 编码规范

遵循 PEP 8 和 PEP 257 标准：

```python
# 好的示例
class DataExtractor:
    """数据提取器类"""

    def __init__(self, config: DataExtractorSettings) -> None:
        self.config = config
        self._cache = {}

    async def extract_data(self, url: str) -> Dict[str, Any]:
        """提取数据

        Args:
            url: 目标URL

        Returns:
            提取的数据字典

        Raises:
            ExtractionError: 提取失败时抛出
        """
        if not url:
            raise ValueError("URL cannot be empty")

        # 实现提取逻辑...
        return result
```

### 类型注解与文档字符串

所有函数和方法都应该有类型注解和 Google 风格的文档字符串：

```python
from typing import Dict, List, Optional, Any

def scrape_webpage(
    url: str,
    method: str = "auto",
    extract_config: Optional[Dict[str, Any]] = None
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
        ExtractionError: 抓取失败
    """
    pass
```

## 性能优化

### 异步编程模式

```python
import asyncio
from typing import List

class BatchProcessor:
    """批处理器"""

    async def process_urls(self, urls: List[str]) -> List[Dict]:
        """批量处理URL"""
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(10)

        async def process_single(url: str) -> Dict:
            async with semaphore:
                return await self._process_single_url(url)

        # 并发执行
        tasks = [process_single(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _process_single_url(self, url: str) -> Dict:
        # 实际处理逻辑
        pass
```

### 缓存策略

```python
from functools import lru_cache
from typing import Optional

class CachedScraper:
    """带缓存的抓取器"""

    @lru_cache(maxsize=128)
    def _get_cached_content(self, url: str) -> Optional[str]:
        """获取缓存内容"""
        # 实现缓存逻辑
        pass

    async def scrape_with_cache(self, url: str) -> Dict:
        """带缓存的抓取"""
        cached = self._get_cached_content(url)
        if cached:
            return {"success": True, "data": cached, "cached": True}

        # 实际抓取
        result = await self._scrape(url)
        if result["success"]:
            self._cache_result(url, result["data"])
        return result
```

### 内存管理

```python
import gc
import weakref
from typing import Dict, Any

class ResourceManager:
    """资源管理器"""

    def __init__(self):
        self._instances = weakref.WeakValueDictionary()
        self._max_instances = 100

    def get_instance(self, instance_id: str) -> Any:
        """获取实例"""
        if instance_id in self._instances:
            return self._instances[instance_id]

        if len(self._instances) >= self._max_instances:
            # 清理最旧的实例
            gc.collect()

        # 创建新实例
        instance = self._create_instance(instance_id)
        self._instances[instance_id] = instance
        return instance
```

## CI/CD 与版本管理

### 持续集成流程

项目配置了完整的 GitHub Actions 工作流，提供自动化的测试、构建和发布功能：

**自动化流程**:

- ✅ 运行完整测试套件
- ✅ 构建分发包
- ✅ 创建 GitHub Release
- ✅ 发布到 PyPI
- ✅ 更新文档

### 多平台测试

- **多平台测试**: Ubuntu, Windows, macOS
- **多版本支持**: Python 3.12, 3.13
- **代码质量**: Ruff linting, MyPy type checking
- **安全扫描**: Bandit security analysis
- **覆盖率报告**: Codecov integration

### 版本管理

项目使用语义化版本控制（Semantic Versioning），版本号格式为 `MAJOR.MINOR.PATCH`：

- **MAJOR**: 重大不兼容变更
- **MINOR**: 新功能增加，向后兼容
- **PATCH**: 错误修复，向后兼容

### 发布流程

```bash
# 1. 更新版本号
vim pyproject.toml  # 更新 version = "x.y.z"

# 2. 更新变更日志
vim CHANGELOG.md    # 添加新版本条目

# 3. 创建发布标签
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to v1.2.3"
git tag v1.2.3
git push origin main --tags

# 4. 构建和检查
uv build
ls dist/

# 5. 版本检查
python -c "import extractor; print(extractor.__version__)"
```

### 自动发布机制

- **标签发布**: 推送 `v*.*.*` 标签自动触发发布
- **PyPI 发布**: 使用 OIDC trusted publishing，无需 API 密钥
- **GitHub Releases**: 自动生成 release notes
- **构建验证**: 发布前完整测试套件验证

## 调试与故障排除

### 调试技巧

#### 日志调试

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self):
        logger.info("Initializing DataExtractor")
        # ...

    async def extract_data(self, url: str):
        logger.info(f"Starting extraction for URL: {url}")
        # ...
        logger.info(f"Extraction completed successfully")
```

#### 异步调试

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

# 在调试环境中运行
asyncio.run(debug_async_function())
```

#### 浏览器调试

```python
# 在测试中启用浏览器调试
@pytest.mark.requires_browser
async def test_with_browser_debugging():
    """启用浏览器调试的测试"""
    from extractor.advanced_features import AntiDetectionScraper

    scraper = AntiDetectionScraper()
    # 添加调试配置
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
# 解决方案：重新安装 Playwright
uv run playwright install --force

# 或使用系统浏览器
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

#### 测试超时问题

```bash
# 解决方案：增加超时时间或跳过慢速测试
uv run pytest -m "not slow" --timeout=300
```

#### 类型检查错误

```bash
# 解决方案：逐步修复类型问题
uv run mypy extractor/ --ignore-missing-imports

# 或使用宽松模式
uv run mypy extractor/ --disable-error-code=var-annotated
```

### 调试命令

```bash
# 查看详细错误信息
uv run pytest -v --tb=long

# 启用调试模式
uv run python -m pdb script.py

# 内存分析
uv run python -m memory_profiler script.py
```

## 开发资源

### 技术文档

- [官方文档](https://docs.astral.sh/uv/)
- [pytest 文档](https://docs.pytest.org/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [MyPy 文档](https://mypy.readthedocs.io/)

### 工具推荐

- **IDE**: PyCharm, VS Code
- **API 测试**: Postman, Insomnia
- **数据库管理**: DBeaver, TablePlus
- **容器**: Docker, Docker Compose
- **监控**: Grafana, Prometheus

---

本开发指南涵盖了 Data Extractor 项目的完整开发流程和最佳实践，为开发者提供详细的技术指导和参考。
