"""infra/ 子包结构与向后兼容性验证。"""

import pytest


class TestInfraPackageExports:
    """验证 infra/ 子包的 __init__.py 导出完整性。"""

    def test_import_cache_manager(self):
        from negentropy.perceives.infra import CacheManager, cache_manager

        assert CacheManager is not None
        assert cache_manager is not None

    def test_import_metrics_collector(self):
        from negentropy.perceives.infra import MetricsCollector, metrics_collector

        assert MetricsCollector is not None
        assert metrics_collector is not None

    def test_import_rate_limiter(self):
        from negentropy.perceives.infra import RateLimiter, rate_limiter

        assert RateLimiter is not None
        assert rate_limiter is not None

    def test_import_retry_manager(self):
        from negentropy.perceives.infra import RetryManager, retry_manager

        assert RetryManager is not None
        assert retry_manager is not None

    def test_import_parsing_functions(self):
        from negentropy.perceives.infra import (
            clean_text,
            extract_domain,
            extract_emails,
            extract_phone_numbers,
            is_valid_url,
            normalize_url,
        )

        assert callable(clean_text)
        assert callable(extract_domain)
        assert callable(extract_emails)
        assert callable(extract_phone_numbers)
        assert callable(is_valid_url)
        assert callable(normalize_url)

    def test_import_parsing_facade_classes(self):
        from negentropy.perceives.infra import TextCleaner, URLValidator

        assert TextCleaner is not None
        assert URLValidator is not None

    def test_import_trace_types(self):
        from negentropy.perceives.infra import (
            TraceEventRecord,
            TraceRecorder,
            active_trace,
            get_recorder,
            trace_event,
        )

        assert TraceEventRecord is not None
        assert TraceRecorder is not None
        assert callable(active_trace)
        assert callable(get_recorder)
        assert callable(trace_event)


class TestInfraBackwardCompatibility:
    """验证旧路径 shim 文件的向后兼容性。"""

    def test_shim_cache_module(self):
        from negentropy.perceives.cache import cache_manager as shim_cm
        from negentropy.perceives.infra import cache_manager as canonical_cm

        assert shim_cm is canonical_cm

    def test_shim_metrics_module(self):
        from negentropy.perceives.metrics import metrics_collector as shim_mc
        from negentropy.perceives.infra import metrics_collector as canonical_mc

        assert shim_mc is canonical_mc

    def test_shim_resilience_module(self):
        from negentropy.perceives.resilience import rate_limiter as shim_rl
        from negentropy.perceives.infra import rate_limiter as canonical_rl

        assert shim_rl is canonical_rl

    def test_shim_parsing_module(self):
        from negentropy.perceives.parsing import URLValidator as shim_uv
        from negentropy.perceives.infra import URLValidator as canonical_uv

        assert shim_uv is canonical_uv

    def test_shim_validation_trace_module(self):
        from negentropy.perceives.validation_trace import trace_event as shim_te
        from negentropy.perceives.infra import trace_event as canonical_te

        assert shim_te is canonical_te

    def test_all_infra_exports_in_dunder_all(self):
        import negentropy.perceives.infra as pkg

        expected = {
            "CacheManager",
            "cache_manager",
            "MetricsCollector",
            "metrics_collector",
            "RateLimiter",
            "RetryManager",
            "rate_limiter",
            "retry_manager",
            "TextCleaner",
            "URLValidator",
            "clean_text",
            "extract_domain",
            "extract_emails",
            "extract_phone_numbers",
            "is_valid_url",
            "normalize_url",
            "TraceEventRecord",
            "TraceRecorder",
            "active_trace",
            "get_recorder",
            "trace_event",
        }
        assert set(pkg.__all__) == expected
