"""MCP 工具响应模型及数据传输对象定义。"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScrapeResponse(BaseModel):
    """Response model for scraping operations."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="被抓取的URL")
    method: str = Field(..., description="使用的抓取方法")
    data: Optional[Dict[str, Any]] = Field(default=None, description="抓取到的数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="页面元数据")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")
    timestamp: datetime = Field(default_factory=datetime.now, description="抓取时间戳")


class BatchScrapeResponse(BaseModel):
    """Response model for batch scraping operations."""

    success: bool = Field(..., description="整体操作是否成功")
    total_urls: int = Field(..., description="总URL数量")
    successful_count: int = Field(..., description="成功抓取的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[ScrapeResponse] = Field(..., description="每个URL的抓取结果")
    summary: Dict[str, Any] = Field(..., description="批量操作摘要信息")


class LinkItem(BaseModel):
    """Individual link item model."""

    url: str = Field(..., description="链接URL")
    text: str = Field(..., description="链接文本")
    is_internal: bool = Field(..., description="是否为内部链接")


class LinksResponse(BaseModel):
    """Response model for link extraction."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    total_links: int = Field(..., description="总链接数量")
    links: List[LinkItem] = Field(..., description="提取的链接列表")
    internal_links_count: int = Field(..., description="内部链接数量")
    external_links_count: int = Field(..., description="外部链接数量")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class PageInfoResponse(BaseModel):
    """Response model for page information."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="页面URL")
    title: Optional[str] = Field(default=None, description="页面标题")
    description: Optional[str] = Field(default=None, description="页面描述")
    status_code: int = Field(..., description="HTTP状态码")
    content_type: Optional[str] = Field(default=None, description="内容类型")
    content_length: Optional[int] = Field(default=None, description="内容长度")
    last_modified: Optional[str] = Field(default=None, description="最后修改时间")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class RobotsResponse(BaseModel):
    """Response model for robots.txt check."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="检查的URL")
    robots_txt_url: str = Field(..., description="robots.txt文件URL")
    robots_content: Optional[str] = Field(default=None, description="robots.txt内容")
    is_allowed: bool = Field(..., description="是否允许抓取")
    user_agent: str = Field(..., description="使用的User-Agent")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class StructuredDataResponse(BaseModel):
    """Response model for structured data extraction."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    data_type: str = Field(..., description="提取的数据类型")
    extracted_data: Dict[str, Any] = Field(..., description="提取的结构化数据")
    data_count: int = Field(..., description="提取的数据项数量")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class MarkdownResponse(BaseModel):
    """Response model for Markdown conversion."""

    success: bool = Field(..., description="操作是否成功")
    url: str = Field(..., description="源页面URL")
    method: str = Field(..., description="使用的转换方法")
    markdown_content: Optional[str] = Field(
        default=None, description="转换后的Markdown内容"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="页面元数据")
    word_count: int = Field(default=0, description="字数统计")
    images_embedded: int = Field(default=0, description="嵌入的图片数量")
    conversion_time: float = Field(..., description="转换耗时（秒）")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class BatchMarkdownResponse(BaseModel):
    """Response model for batch Markdown conversion."""

    success: bool = Field(..., description="整体操作是否成功")
    total_urls: int = Field(..., description="总URL数量")
    successful_count: int = Field(..., description="成功转换的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[MarkdownResponse] = Field(..., description="每个URL的转换结果")
    total_word_count: int = Field(default=0, description="总字数")
    total_conversion_time: float = Field(..., description="总转换时间（秒）")


class PDFResponse(BaseModel):
    """Response model for PDF conversion with enhanced features."""

    success: bool = Field(..., description="操作是否成功")
    pdf_source: str = Field(..., description="PDF源路径或URL")
    method: str = Field(..., description="使用的转换方法")
    output_format: str = Field(..., description="输出格式")
    content: Optional[str] = Field(default=None, description="转换后的内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="PDF元数据")
    page_count: int = Field(default=0, description="页数")
    word_count: int = Field(default=0, description="字数统计")
    conversion_time: float = Field(..., description="转换耗时（秒）")
    enhanced_assets: Optional[Dict[str, Any]] = Field(
        default=None, description="增强资源提取统计（图像、表格、公式）"
    )
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")


class BatchPDFResponse(BaseModel):
    """Response model for batch PDF conversion."""

    success: bool = Field(..., description="整体操作是否成功")
    total_pdfs: int = Field(..., description="总PDF数量")
    successful_count: int = Field(..., description="成功转换的数量")
    failed_count: int = Field(..., description="失败的数量")
    results: List[PDFResponse] = Field(..., description="每个PDF的转换结果")
    total_pages: int = Field(default=0, description="总页数")
    total_word_count: int = Field(default=0, description="总字数")
    total_conversion_time: float = Field(..., description="总转换时间（秒）")


class MetricsResponse(BaseModel):
    """Response model for server metrics."""

    success: bool = Field(..., description="操作是否成功")
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    success_rate: float = Field(..., description="成功率")
    average_response_time: float = Field(..., description="平均响应时间（秒）")
    uptime_seconds: float = Field(..., description="运行时间（秒）")
    cache_stats: Dict[str, Any] = Field(..., description="缓存统计")
    method_usage: Dict[str, int] = Field(..., description="方法使用统计")
    error_categories: Dict[str, int] = Field(..., description="错误分类统计")


class CacheOperationResponse(BaseModel):
    """Response model for cache clearing."""

    success: bool = Field(..., description="操作是否成功")
    cleared_items: int = Field(..., description="清理的缓存项数量")
    cache_size_before: int = Field(..., description="清理前缓存大小")
    cache_size_after: int = Field(..., description="清理后缓存大小")
    operation_time: float = Field(..., description="操作耗时（秒）")
    message: str = Field(..., description="操作结果消息")


# --- 内部数据传输对象 ---


@dataclass
class ScrapingResult:
    """Standard result format for scraping operations."""

    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None
    method_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result
