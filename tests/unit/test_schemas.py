"""响应模型 (schemas) 单元测试。"""

import pytest
from datetime import datetime

from extractor.schemas import (
    ScrapeResponse,
    BatchScrapeResponse,
    LinkItem,
    LinksResponse,
    PageInfoResponse,
    RobotsResponse,
    StructuredDataResponse,
    MarkdownResponse,
    BatchMarkdownResponse,
    PDFResponse,
    BatchPDFResponse,
    MetricsResponse,
    CacheOperationResponse,
)


class TestScrapeResponse:
    """ScrapeResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = ScrapeResponse(success=True, url="https://example.com", method="simple")
        assert resp.success is True
        assert resp.url == "https://example.com"
        assert resp.method == "simple"

    def test_optional_fields_default_none(self):
        """可选字段默认值为 None。"""
        resp = ScrapeResponse(success=False, url="https://example.com", method="auto")
        assert resp.data is None
        assert resp.metadata is None
        assert resp.error is None

    def test_timestamp_auto_generated(self):
        """时间戳自动生成。"""
        resp = ScrapeResponse(success=True, url="https://example.com", method="auto")
        assert isinstance(resp.timestamp, datetime)

    def test_with_all_fields(self):
        """全字段赋值。"""
        resp = ScrapeResponse(
            success=True,
            url="https://example.com",
            method="selenium",
            data={"title": "Test"},
            metadata={"content_length": 100},
            error=None,
        )
        assert resp.data == {"title": "Test"}
        assert resp.metadata == {"content_length": 100}

    def test_serialization(self):
        """序列化测试。"""
        resp = ScrapeResponse(success=True, url="https://example.com", method="auto")
        data = resp.model_dump()
        assert "success" in data
        assert "url" in data
        assert "timestamp" in data


class TestBatchScrapeResponse:
    """BatchScrapeResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        single = ScrapeResponse(success=True, url="https://a.com", method="auto")
        resp = BatchScrapeResponse(
            success=True,
            total_urls=1,
            successful_count=1,
            failed_count=0,
            results=[single],
            summary={"total_time": 1.0},
        )
        assert resp.total_urls == 1
        assert len(resp.results) == 1

    def test_nested_results(self):
        """嵌套结果列表。"""
        results = [
            ScrapeResponse(success=True, url=f"https://example.com/{i}", method="auto")
            for i in range(3)
        ]
        resp = BatchScrapeResponse(
            success=True,
            total_urls=3,
            successful_count=3,
            failed_count=0,
            results=results,
            summary={},
        )
        assert len(resp.results) == 3


class TestLinkItem:
    """LinkItem 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        item = LinkItem(url="https://example.com", text="Example", is_internal=True)
        assert item.url == "https://example.com"
        assert item.text == "Example"
        assert item.is_internal is True


class TestLinksResponse:
    """LinksResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = LinksResponse(
            success=True,
            url="https://example.com",
            total_links=2,
            links=[
                LinkItem(url="https://a.com", text="A", is_internal=True),
                LinkItem(url="https://b.com", text="B", is_internal=False),
            ],
            internal_links_count=1,
            external_links_count=1,
        )
        assert resp.total_links == 2
        assert resp.error is None


class TestPageInfoResponse:
    """PageInfoResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = PageInfoResponse(
            success=True, url="https://example.com", status_code=200
        )
        assert resp.status_code == 200
        assert resp.title is None
        assert resp.description is None

    def test_with_all_fields(self):
        """全字段赋值。"""
        resp = PageInfoResponse(
            success=True,
            url="https://example.com",
            status_code=200,
            title="Test",
            description="Desc",
            content_type="text/html",
            content_length=1024,
            last_modified="2024-01-01",
        )
        assert resp.title == "Test"
        assert resp.content_length == 1024


class TestRobotsResponse:
    """RobotsResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = RobotsResponse(
            success=True,
            url="https://example.com",
            robots_txt_url="https://example.com/robots.txt",
            is_allowed=True,
            user_agent="*",
        )
        assert resp.is_allowed is True
        assert resp.robots_content is None


class TestStructuredDataResponse:
    """StructuredDataResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = StructuredDataResponse(
            success=True,
            url="https://example.com",
            data_type="contact",
            extracted_data={"emails": ["a@b.com"]},
            data_count=1,
        )
        assert resp.data_type == "contact"
        assert resp.data_count == 1


class TestMarkdownResponse:
    """MarkdownResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = MarkdownResponse(
            success=True,
            url="https://example.com",
            method="simple",
            conversion_time=0.5,
        )
        assert resp.word_count == 0
        assert resp.images_embedded == 0
        assert resp.markdown_content is None

    def test_with_content(self):
        """含内容的响应。"""
        resp = MarkdownResponse(
            success=True,
            url="https://example.com",
            method="simple",
            markdown_content="# Title\n\nContent",
            word_count=2,
            images_embedded=0,
            conversion_time=1.0,
        )
        assert resp.markdown_content.startswith("# Title")


class TestBatchMarkdownResponse:
    """BatchMarkdownResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        single = MarkdownResponse(
            success=True, url="https://a.com", method="auto", conversion_time=0.1
        )
        resp = BatchMarkdownResponse(
            success=True,
            total_urls=1,
            successful_count=1,
            failed_count=0,
            results=[single],
            total_conversion_time=0.1,
        )
        assert resp.total_word_count == 0


class TestPDFResponse:
    """PDFResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = PDFResponse(
            success=True,
            pdf_source="/path/to/file.pdf",
            method="pymupdf",
            output_format="markdown",
            conversion_time=2.0,
        )
        assert resp.page_count == 0
        assert resp.word_count == 0
        assert resp.enhanced_assets is None

    def test_with_enhanced_assets(self):
        """含增强资源的响应。"""
        resp = PDFResponse(
            success=True,
            pdf_source="https://example.com/file.pdf",
            method="auto",
            output_format="markdown",
            conversion_time=3.0,
            enhanced_assets={"images": 5, "tables": 2, "formulas": 1},
        )
        assert resp.enhanced_assets["images"] == 5


class TestBatchPDFResponse:
    """BatchPDFResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        single = PDFResponse(
            success=True,
            pdf_source="a.pdf",
            method="auto",
            output_format="markdown",
            conversion_time=1.0,
        )
        resp = BatchPDFResponse(
            success=True,
            total_pdfs=1,
            successful_count=1,
            failed_count=0,
            results=[single],
            total_conversion_time=1.0,
        )
        assert resp.total_pages == 0
        assert resp.total_word_count == 0


class TestMetricsResponse:
    """MetricsResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = MetricsResponse(
            success=True,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            success_rate=0.95,
            average_response_time=1.5,
            uptime_seconds=3600.0,
            cache_stats={"hits": 50, "misses": 20},
            method_usage={"simple": 60, "selenium": 40},
            error_categories={"timeout": 3, "connection": 2},
        )
        assert resp.success_rate == 0.95
        assert resp.cache_stats["hits"] == 50


class TestCacheOperationResponse:
    """CacheOperationResponse 模型测试。"""

    def test_required_fields(self):
        """必填字段校验。"""
        resp = CacheOperationResponse(
            success=True,
            cleared_items=10,
            cache_size_before=10,
            cache_size_after=0,
            operation_time=0.01,
            message="Cache cleared successfully",
        )
        assert resp.cleared_items == 10
        assert resp.cache_size_after == 0


class TestBackwardCompatibility:
    """向后兼容性测试：确认所有模型可通过垫片路径导入。"""

    def test_all_models_importable(self):
        """所有 13 个模型均可正常导入。"""
        from extractor.schemas import (
            ScrapeResponse,
            BatchScrapeResponse,
            LinkItem,
            LinksResponse,
            PageInfoResponse,
            RobotsResponse,
            StructuredDataResponse,
            MarkdownResponse,
            BatchMarkdownResponse,
            PDFResponse,
            BatchPDFResponse,
            MetricsResponse,
            CacheOperationResponse,
        )

        assert ScrapeResponse is not None
        assert CacheOperationResponse is not None
