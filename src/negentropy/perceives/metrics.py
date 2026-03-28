"""抓取指标收集与统计。"""

from typing import Any, Dict, Optional

from .url_utils import URLValidator


class MetricsCollector:
    """抓取指标收集器。"""

    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0,
            "methods_used": {},
            "error_categories": {},
            "domains_scraped": set(),
        }

    def record_request(
        self,
        url: str,
        success: bool,
        duration_ms: int,
        method: str,
        error_category: Optional[str] = None,
    ) -> None:
        """记录抓取请求指标。"""
        self.metrics["total_requests"] += 1
        self.metrics["total_duration_ms"] += duration_ms

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            if error_category:
                self.metrics["error_categories"][error_category] = (
                    self.metrics["error_categories"].get(error_category, 0) + 1
                )

        # Track method usage
        self.metrics["methods_used"][method] = (
            self.metrics["methods_used"].get(method, 0) + 1
        )

        # Track domains
        domain = URLValidator.extract_domain(url)
        self.metrics["domains_scraped"].add(domain)

    def get_stats(self) -> Dict[str, Any]:
        """获取当前指标统计。"""
        stats = self.metrics.copy()
        stats["domains_scraped"] = list(stats["domains_scraped"])
        stats["success_rate"] = self.metrics["successful_requests"] / max(
            1, self.metrics["total_requests"]
        )
        stats["average_duration_ms"] = self.metrics["total_duration_ms"] / max(
            1, self.metrics["total_requests"]
        )
        # 兼容 MetricsResponse schema 的字段名
        stats["average_response_time"] = stats["average_duration_ms"] / 1000.0
        stats["method_usage"] = stats["methods_used"]
        return stats

    def reset(self) -> None:
        """重置所有指标。"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration_ms": 0,
            "methods_used": {},
            "error_categories": {},
            "domains_scraped": set(),
        }


metrics_collector = MetricsCollector()
