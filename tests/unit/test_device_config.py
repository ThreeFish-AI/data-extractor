"""设备感知配置策略模块的单元测试。

测试策略：
- 使用 mock 控制硬件检测结果，验证不同设备下的配置降级和优化逻辑
- 验证缓存键的设备段生成
"""

from unittest.mock import patch

import pytest

from extractor.hardware import DeviceType
from extractor.pdf.device_config import (
    DoclingDeviceConfig,
    _apply_cuda_optimizations,
    _apply_mps_constraints,
    resolve_device_config,
)


# ============================================================
# DoclingDeviceConfig 数据类
# ============================================================
class TestDoclingDeviceConfig:
    """验证 DoclingDeviceConfig 数据类的字段与属性。"""

    def test_defaults(self) -> None:
        config = DoclingDeviceConfig(device="cpu")
        assert config.device == "cpu"
        assert config.num_threads == 4
        assert config.do_formula_enrichment is True
        assert config.do_table_structure is True
        assert config.table_mode == "accurate"
        assert config.use_flash_attention is False
        assert config.device_type == DeviceType.CPU
        assert config.adjustments == {}

    def test_cache_key_segment(self) -> None:
        config = DoclingDeviceConfig(device="mps", num_threads=8, use_flash_attention=False)
        segment = config.cache_key_segment
        assert "dev=mps" in segment
        assert "threads=8" in segment
        assert "fa2=False" in segment

    def test_different_devices_different_cache_keys(self) -> None:
        c1 = DoclingDeviceConfig(device="cpu")
        c2 = DoclingDeviceConfig(device="mps")
        assert c1.cache_key_segment != c2.cache_key_segment

    def test_same_device_same_cache_key(self) -> None:
        c1 = DoclingDeviceConfig(device="cuda", num_threads=4)
        c2 = DoclingDeviceConfig(device="cuda", num_threads=4)
        assert c1.cache_key_segment == c2.cache_key_segment


# ============================================================
# MPS 限制策略
# ============================================================
class TestMPSConstraints:
    """验证 Apple Silicon MPS 限制处理。"""

    def test_mps_disables_formula_enrichment(self) -> None:
        """MPS 应主动禁用 formula enrichment。"""
        config = DoclingDeviceConfig(
            device="mps",
            device_type=DeviceType.MPS,
            do_formula_enrichment=True,
        )
        _apply_mps_constraints(config)
        assert config.do_formula_enrichment is False
        assert "formula_enrichment" in config.adjustments

    def test_mps_preserves_table_structure(self) -> None:
        """MPS 不应影响 table structure 配置。"""
        config = DoclingDeviceConfig(
            device="mps",
            device_type=DeviceType.MPS,
            do_table_structure=True,
        )
        _apply_mps_constraints(config)
        assert config.do_table_structure is True

    def test_mps_disables_flash_attention(self) -> None:
        """MPS 应禁用 Flash Attention 2。"""
        config = DoclingDeviceConfig(
            device="mps",
            device_type=DeviceType.MPS,
            use_flash_attention=True,
        )
        _apply_mps_constraints(config)
        assert config.use_flash_attention is False

    def test_mps_no_adjustment_when_formula_disabled(self) -> None:
        """formula 已禁用时不应记录调整。"""
        config = DoclingDeviceConfig(
            device="mps",
            device_type=DeviceType.MPS,
            do_formula_enrichment=False,
        )
        _apply_mps_constraints(config)
        assert "formula_enrichment" not in config.adjustments


# ============================================================
# CUDA 优化策略
# ============================================================
class TestCUDAOptimizations:
    """验证 NVIDIA CUDA 优化处理。"""

    @patch("extractor.pdf.device_config._check_flash_attention_available", return_value=True)
    def test_cuda_enables_flash_attention(self, _mock: object) -> None:
        """CUDA + flash_attn 已安装时应启用 FA2。"""
        config = DoclingDeviceConfig(device="cuda", device_type=DeviceType.CUDA)
        _apply_cuda_optimizations(config)
        assert config.use_flash_attention is True
        assert "flash_attention" in config.adjustments

    @patch("extractor.pdf.device_config._check_flash_attention_available", return_value=False)
    def test_cuda_no_flash_attention_when_missing(self, _mock: object) -> None:
        """CUDA + flash_attn 未安装时应跳过 FA2。"""
        config = DoclingDeviceConfig(device="cuda", device_type=DeviceType.CUDA)
        _apply_cuda_optimizations(config)
        assert config.use_flash_attention is False

    def test_cuda_preserves_all_features(self) -> None:
        """CUDA 应保留所有 Docling 功能。"""
        config = DoclingDeviceConfig(
            device="cuda",
            device_type=DeviceType.CUDA,
            do_formula_enrichment=True,
            do_table_structure=True,
        )
        _apply_cuda_optimizations(config)
        assert config.do_formula_enrichment is True
        assert config.do_table_structure is True


# ============================================================
# resolve_device_config 集成逻辑
# ============================================================
class TestResolveDeviceConfig:
    """验证 resolve_device_config 核心入口。"""

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="cpu")
    def test_cpu_no_adjustments(self, _mock: object) -> None:
        """CPU 设备应无配置降级。"""
        config = resolve_device_config(device_preference="cpu")
        assert config.device == "cpu"
        assert config.do_formula_enrichment is True
        assert config.use_flash_attention is False

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="mps")
    def test_mps_applies_constraints(self, _mock: object) -> None:
        """MPS 设备应自动应用限制。"""
        config = resolve_device_config(device_preference="mps", enable_formula=True)
        assert config.device == "mps"
        assert config.device_type == DeviceType.MPS
        assert config.do_formula_enrichment is False
        assert "formula_enrichment" in config.adjustments

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="cuda")
    @patch("extractor.pdf.device_config._check_flash_attention_available", return_value=True)
    def test_cuda_applies_optimizations(self, _mock_fa: object, _mock_dev: object) -> None:
        """CUDA 设备应启用优化。"""
        config = resolve_device_config(device_preference="cuda")
        assert config.device == "cuda"
        assert config.device_type == DeviceType.CUDA
        assert config.use_flash_attention is True
        assert config.do_formula_enrichment is True

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="cpu")
    def test_explicit_cpu_preference(self, _mock: object) -> None:
        """显式指定 CPU 应跳过 GPU 优化。"""
        config = resolve_device_config(device_preference="cpu")
        assert config.device_type == DeviceType.CPU
        assert config.use_flash_attention is False

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="mps")
    def test_custom_num_threads(self, _mock: object) -> None:
        """应正确传递自定义线程数。"""
        config = resolve_device_config(device_preference="mps", num_threads=8)
        assert config.num_threads == 8

    @patch("extractor.pdf.device_config.get_device_for_docling", return_value="xpu")
    def test_xpu_no_special_handling(self, _mock: object) -> None:
        """XPU 使用默认配置，无特殊调整。"""
        config = resolve_device_config(device_preference="xpu")
        assert config.device == "xpu"
        assert config.do_formula_enrichment is True
        assert config.use_flash_attention is False
