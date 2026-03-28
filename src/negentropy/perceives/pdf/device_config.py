"""设备感知的 Docling 配置策略模块。

根据运行时检测到的硬件设备（MPS/CUDA/CPU/XPU）自动调整 Docling
管道配置，处理各平台已知限制并启用对应优化。

Design Pattern: Strategy Pattern — 将设备特定的配置决策封装为独立策略

已知平台限制（Docling 2.12.0+）:
    - MPS: Formula enrichment 不兼容，启用时整个管道回退 CPU
    - MPS: TableFormer 被禁用，Docling 内部透明回退 CPU
    - CUDA: 支持 Flash Attention 2 加速
    - MPS/XPU: 不支持 Flash Attention 2

References:
    [1] Docling GPU 支持文档, https://docling-project.github.io/docling/usage/gpu/
    [2] Docling AcceleratorDevice 源码, https://github.com/docling-project/docling/blob/main/docling/datamodel/accelerator_options.py
    [3] MPS + Formula Enrichment 不兼容讨论, https://github.com/docling-project/docling/discussions/2505
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from .hardware import DeviceType, detect_device, get_device_for_docling

logger = logging.getLogger(__name__)


@dataclass
class DoclingDeviceConfig:
    """设备感知的 Docling 配置参数集。

    封装了特定设备下 Docling 管道应使用的所有配置参数，
    包括加速选项、功能降级和设备特定优化。
    """

    device: str  # Docling AcceleratorDevice 值
    num_threads: int = 4
    do_formula_enrichment: bool = True
    do_table_structure: bool = True
    table_mode: str = "accurate"
    use_flash_attention: bool = False
    device_type: DeviceType = DeviceType.CPU
    adjustments: Dict[str, str] = field(default_factory=dict)

    @property
    def cache_key_segment(self) -> str:
        """生成用于 converter 缓存键的设备段。"""
        return f"dev={self.device}|threads={self.num_threads}|fa2={self.use_flash_attention}"


def resolve_device_config(
    device_preference: Optional[str] = None,
    num_threads: int = 4,
    enable_formula: bool = True,
    enable_table: bool = True,
    table_mode: str = "accurate",
) -> DoclingDeviceConfig:
    """根据硬件环境解析最优 Docling 配置。

    此函数是设备适配的核心入口：
    1. 解析设备偏好（auto 时自动检测）
    2. 根据设备类型应用已知限制的降级策略
    3. 启用设备特定优化（如 CUDA Flash Attention 2）
    4. 记录所有调整决策用于可观测性

    Args:
        device_preference: 设备偏好 ('auto', 'cpu', 'cuda', 'mps', 'xpu')
        num_threads: CPU 推理线程数
        enable_formula: 是否请求公式提取
        enable_table: 是否请求表格提取
        table_mode: TableFormer 模式 ('accurate', 'fast')

    Returns:
        设备适配后的完整配置
    """
    device_str = get_device_for_docling(device_preference)

    try:
        device_type = DeviceType(device_str)
    except ValueError:
        device_type = DeviceType.CPU

    config = DoclingDeviceConfig(
        device=device_str,
        device_type=device_type,
        num_threads=num_threads,
        do_formula_enrichment=enable_formula,
        do_table_structure=enable_table,
        table_mode=table_mode,
    )

    if device_type == DeviceType.MPS:
        _apply_mps_constraints(config)
    elif device_type == DeviceType.CUDA:
        _apply_cuda_optimizations(config)

    if config.adjustments:
        for key, reason in config.adjustments.items():
            logger.info("Docling 配置调整 [%s]: %s — %s", device_str, key, reason)
    else:
        logger.info("Docling 设备配置: %s (无降级调整)", device_str)

    return config


def _apply_mps_constraints(config: DoclingDeviceConfig) -> None:
    """应用 Apple Silicon MPS 的已知限制。

    MPS 限制（Docling 2.12.0+ 官方文档）：
    - Formula enrichment: 与 MPS 不兼容，启用时整个管道回退 CPU
    - TableFormer: MPS 上被禁用，Docling 内部透明回退 CPU（无需干预）
    - Flash Attention 2: 仅 CUDA 支持

    策略: 主动禁用 formula enrichment 以避免 Docling 将整个管道回退到 CPU。
    公式通过 Markdown 正则提取补偿（已有 ``_extract_formulas`` 实现）。
    """
    if config.do_formula_enrichment:
        config.do_formula_enrichment = False
        config.adjustments["formula_enrichment"] = (
            "MPS 与 formula enrichment 不兼容，已禁用以保持 GPU 加速；"
            "公式将通过 Markdown 正则提取替代"
        )

    config.use_flash_attention = False


def _apply_cuda_optimizations(config: DoclingDeviceConfig) -> None:
    """应用 NVIDIA CUDA 特定优化。

    CUDA 优化：
    - Flash Attention 2: 显著提升 Transformer 推理性能（需安装 flash-attn）
    - 所有 Docling 功能均完全支持
    """
    config.use_flash_attention = _check_flash_attention_available()
    if config.use_flash_attention:
        config.adjustments["flash_attention"] = "Flash Attention 2 已启用"


def _check_flash_attention_available() -> bool:
    """检测 Flash Attention 2 是否可用。"""
    try:
        import flash_attn  # noqa: F401

        return True
    except ImportError:
        return False
