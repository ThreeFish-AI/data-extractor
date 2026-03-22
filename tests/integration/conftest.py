"""端到端集成测试共用 fixture。

为 test_e2e_*.py 系列测试文件提供共享的 fixture，
避免各文件重复定义 MCP 工具字典与 PDF 处理器实例。
"""

import pytest
import pytest_asyncio

from extractor.server import (
    app,
    create_pdf_processor,
)


@pytest.fixture
def pdf_processor():
    """创建 PDF 处理器实例用于测试。"""
    return create_pdf_processor()


@pytest_asyncio.fixture
async def e2e_tools():
    """获取所有 MCP 工具的名称-工具映射字典，用于端到端测试。"""
    return {t.name: t for t in await app.list_tools()}
