"""端到端集成测试共用 fixture。

为 test_e2e_*.py 系列测试文件提供共享的 fixture，
避免各文件重复定义 MCP 工具字典与 PDF 处理器实例。
"""

import logging
import time

import pytest
import pytest_asyncio

from negentropy.perceives.tools import create_pdf_processor
from tests.integration.tooling import get_tool_map

logger = logging.getLogger(__name__)


@pytest.fixture
def pdf_processor():
    """创建 PDF 处理器实例用于测试。"""
    return create_pdf_processor()


@pytest_asyncio.fixture
async def e2e_tools():
    """获取所有 MCP 工具的名称-工具映射字典，用于端到端测试。"""
    return await get_tool_map()


# ── GPU 感知 Session 级 Fixture ──────────────────────────────────


@pytest.fixture(scope="session")
def detected_gpu_device():
    """Session 级 fixture：返回检测到的 GPU 设备类型。

    在 session 开始时执行一次硬件检测并记录详细信息到测试日志。
    用于 GPU 相关测试的前置条件判断。
    """
    from negentropy.perceives.pdf.hardware import detect_device, get_hardware_info

    device = detect_device()
    info = get_hardware_info()
    logger.info(
        "硬件检测结果: device=%s, name=%s, memory=%.1fGB, platform=%s",
        info.device_type.value,
        info.device_name or "N/A",
        info.memory_gb or 0.0,
        info.platform_info,
    )
    return device


@pytest.fixture(scope="session")
def gpu_docling_engine(detected_gpu_device):
    """Session 级 fixture：创建显式指定 GPU 设备的 DoclingEngine 实例。

    关键行为：
    1. 显式传递检测到的设备类型（非 'auto'），确保设备选择可审计
    2. 后续所有测试类共享同一实例（通过类级 _converters 缓存）

    注意：此 fixture 仅在 ``detected_gpu_device.is_gpu`` 为 True 时有意义，
    由 ``skip_no_gpu`` 标记在测试层面控制跳过逻辑。
    """
    from negentropy.perceives.pdf.docling_engine import DoclingEngine

    engine = DoclingEngine(device=detected_gpu_device.value)

    device_config = engine._resolve_device_config()
    logger.info(
        "DoclingEngine 设备配置: device=%s, device_type=%s, "
        "formula_enrichment=%s, flash_attention=%s",
        device_config.device,
        device_config.device_type.value,
        device_config.do_formula_enrichment,
        device_config.use_flash_attention,
    )

    return engine


@pytest.fixture(scope="session")
def warm_docling_converter(gpu_docling_engine):
    """Session 级 fixture：预热 Docling Converter（触发模型加载）。

    首次调用 ``_get_converter()`` 会加载 AI 模型（约 10-30 秒），
    此 fixture 在 session 开始时完成这一耗时操作，
    后续测试直接使用已缓存的 converter。

    返回预热耗时（秒）供测试日志记录。
    """
    from negentropy.perceives.pdf.docling_engine import DoclingEngine

    if not DoclingEngine.is_available():
        pytest.skip("Docling 未安装，跳过 converter 预热")

    t0 = time.perf_counter()
    converter = gpu_docling_engine._get_converter()
    elapsed = time.perf_counter() - t0

    logger.info("Docling Converter 预热完成: %.2f 秒", elapsed)
    assert converter is not None, "Converter 预热失败：返回 None"

    return elapsed
