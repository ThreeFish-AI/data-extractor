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

## 概述

Data Extractor 采用现代化的 Python 开发工具链，基于 uv 包管理器构建高效的开发环境。本文档提供完整的开发指南、最佳实践和代码质量保障机制。

## 环境设置

### 系统要求

- **Python**: 3.12+ （推荐 3.13）
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最少 4GB RAM
- **存储**: 最少 10GB 可用空间

### 快速初始化

```bash
# 使用提供的脚本快速设置（推荐）
./scripts/setup.sh

# 验证环境设置
uv --version
python --version
```

### 手动环境配置

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

## 开发工具链

### 包管理器：uv

```bash
# 安装依赖
uv sync

# 安装特定依赖
uv add requests

# 安装开发依赖
uv sync --extra dev

# 运行命令
uv run python script.py
uv run pytest
```

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

### 测试工具

**pytest**：测试框架

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/unit/test_config.py

# 运行带覆盖率的测试
uv run pytest --cov=extractor --cov-report=html

# 并行运行测试
uv run pytest -n auto
```

## 开发工作流

### 1. 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发功能
# 编辑代码文件...

# 3. 运行测试
uv run pytest tests/unit/

# 4. 代码质量检查
uv run ruff check .
uv run mypy extractor/
uv run pre-commit run --all-files

# 5. 提交代码
git add .
git commit -m "feat: add new feature"

# 6. 推送分支
git push origin feature/new-feature
```

### 2. 代码质量检查

在提交前，确保通过所有质量检查：

```bash
# 完整的质量检查流程
uv run ruff check . && uv run ruff format . && uv run mypy extractor/ && uv run pytest
```

### 3. 测试策略

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

## 代码规范

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

### 类型注解

所有函数和方法都应该有类型注解：

```python
from typing import Dict, List, Optional, Any

def process_data(
    data: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理数据"""
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
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

## 测试指南

### 单元测试

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

### 集成测试

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

## 调试技巧

### 日志调试

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

# 在调试环境中运行
asyncio.run(debug_async_function())
```

### 浏览器调试

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

## 性能优化

### 1. 异步编程最佳实践

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

### 2. 缓存策略

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

### 3. 内存管理

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

## 部署准备

### 1. 构建分发包

```bash
# 构建分发包
uv build

# 检查构建结果
ls dist/
```

### 2. Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && \
    uv sync --frozen && \
    uv pip install .

COPY extractor/ extractor/
COPY scripts/ scripts/

EXPOSE 8000
CMD ["uv", "run", "data-extractor"]
```

### 3. 环境变量配置

```bash
# 生产环境变量
export DATA_EXTRACTOR_LOG_LEVEL=INFO
export DATA_EXTRACTOR_CONCURRENT_REQUESTS=32
export DATA_EXTRACTOR_ENABLE_JAVASCRIPT=true
export DATA_EXTRACTOR_BROWSER_HEADLESS=true
```

## 故障排除

### 常见问题

**问题 1: 浏览器驱动问题**

```bash
# 解决方案：重新安装 Playwright
uv run playwright install --force

# 或使用系统浏览器
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

**问题 2: 测试超时**

```bash
# 解决方案：增加超时时间或跳过慢速测试
uv run pytest -m "not slow" --timeout=300
```

**问题 3: 类型检查错误**

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

### 文档

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
