"""Service management MCP tools: metrics and cache."""

import time

from ..infra import cache_manager, metrics_collector
from ..schemas import CacheOperationResponse, MetricsResponse
from ._registry import app


@app.tool()
async def get_server_metrics() -> MetricsResponse:
    """
    Get server performance metrics and statistics.

    Args: 无需参数，返回服务器性能指标和统计信息

    Returns information about:
    - Request counts and success rates
    - Performance metrics
    - Method usage statistics
    - Error categories
    - Cache statistics
    - Server configuration details

    Returns:
        MetricsResponse object containing detailed server metrics including scraping performance,
        cache statistics, server configuration, and real-time statistics.
    """
    try:
        metrics = metrics_collector.get_stats()
        cache_stats = cache_manager.stats()

        return MetricsResponse(
            success=True,
            total_requests=metrics.get("total_requests", 0),
            successful_requests=metrics.get("successful_requests", 0),
            failed_requests=metrics.get("failed_requests", 0),
            success_rate=metrics.get("success_rate", 0.0),
            average_response_time=metrics.get("average_response_time", 0.0),
            uptime_seconds=metrics.get("uptime_seconds", 0.0),
            cache_stats=cache_stats,
            method_usage=metrics.get("method_usage", {}),
            error_categories=metrics.get("error_categories", {}),
        )
    except Exception:
        return MetricsResponse(
            success=False,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            success_rate=0.0,
            average_response_time=0.0,
            uptime_seconds=0.0,
            cache_stats={},
            method_usage={},
            error_categories={},
        )


@app.tool()
async def clear_cache() -> CacheOperationResponse:
    """
    Clear the scraping results cache.

    Args: 无需参数，清理全局抓取结果缓存

    This removes all cached scraping results, forcing fresh requests
    for all subsequent scraping operations.

    Returns:
        CacheOperationResponse object containing success status and cache clearing confirmation message.
        Useful for forcing fresh data retrieval and managing memory usage.
    """
    try:
        start_time = time.time()
        cache_size_before = cache_manager.size()
        cleared_items = cache_manager.clear()
        cache_size_after = 0
        operation_time = time.time() - start_time

        return CacheOperationResponse(
            success=True,
            cleared_items=cleared_items,
            cache_size_before=cache_size_before,
            cache_size_after=cache_size_after,
            operation_time=operation_time,
            message="Cache cleared successfully",
        )
    except Exception as e:
        return CacheOperationResponse(
            success=False,
            cleared_items=0,
            cache_size_before=0,
            cache_size_after=0,
            operation_time=0.0,
            message=f"Error clearing cache: {str(e)}",
        )
