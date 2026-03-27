"""Python SDK tests for the document-reader facade."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from extractor.sdk import (
    DocumentReaderClient,
    DocumentReaderConnectionError,
    DocumentReaderToolError,
)


class TestDocumentReaderClient:
    """测试 document-reader Python SDK。"""

    @pytest.mark.asyncio
    async def test_connect_and_close(self):
        """connect/close 应委托给底层 FastMCP Client。"""
        with (
            patch("extractor.sdk.StreamableHttpTransport") as transport_cls,
            patch("extractor.sdk.Client") as client_cls,
        ):
            mock_client = AsyncMock()
            client_cls.return_value = mock_client

            client = DocumentReaderClient("http://localhost:8081/mcp")
            await client.connect()
            await client.close()

            transport_cls.assert_called_once_with(
                url="http://localhost:8081/mcp", headers=None, auth=None
            )
            mock_client.__aenter__.assert_awaited_once()
            mock_client.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_tool_delegates(self):
        """call_tool 应透传工具名和参数。"""
        with patch("extractor.sdk.StreamableHttpTransport"), patch(
            "extractor.sdk.Client"
        ) as client_cls:
            mock_client = AsyncMock()
            mock_client.call_tool = AsyncMock(return_value={"success": True})
            client_cls.return_value = mock_client

            client = DocumentReaderClient()
            result = await client.call_tool("scrape_webpage", {"url": "https://a.com"})

            assert result == {"success": True}
            mock_client.__aenter__.assert_awaited_once()
            mock_client.call_tool.assert_awaited_once_with(
                "scrape_webpage",
                {"url": "https://a.com"},
                timeout=None,
                raise_on_error=True,
                meta=None,
            )

    @pytest.mark.asyncio
    async def test_scrape_webpage_helper(self):
        """快捷方法应调用统一的 call_tool 接口。"""
        with patch.object(
            DocumentReaderClient,
            "call_tool",
            new_callable=AsyncMock,
            return_value={"success": True},
        ) as mock_call_tool:
            client = DocumentReaderClient()
            result = await client.scrape_webpage(
                url="https://example.com",
                method="simple",
                extract_config={"title": "h1"},
                wait_for_element="body",
            )

            assert result == {"success": True}
            mock_call_tool.assert_awaited_once_with(
                "scrape_webpage",
                {
                    "url": "https://example.com",
                    "method": "simple",
                    "extract_config": {"title": "h1"},
                    "wait_for_element": "body",
                },
            )

    @pytest.mark.asyncio
    async def test_list_tools_returns_server_tools(self):
        """list_tools 应返回底层 Client 的结果。"""
        with patch("extractor.sdk.StreamableHttpTransport"), patch(
            "extractor.sdk.Client"
        ) as client_cls:
            tool = SimpleNamespace(name="scrape_webpage")
            mock_client = AsyncMock()
            mock_client.list_tools = AsyncMock(return_value=[tool])
            client_cls.return_value = mock_client

            client = DocumentReaderClient()
            tools = await client.list_tools()

            assert tools == [tool]

    @pytest.mark.asyncio
    async def test_connect_wraps_connection_errors(self):
        """连接错误应映射为项目异常。"""
        with patch("extractor.sdk.StreamableHttpTransport"), patch(
            "extractor.sdk.Client"
        ) as client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.side_effect = RuntimeError("boom")
            client_cls.return_value = mock_client

            client = DocumentReaderClient()
            with pytest.raises(DocumentReaderConnectionError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_call_tool_wraps_tool_errors(self):
        """工具调用错误应映射为项目异常。"""
        with patch("extractor.sdk.StreamableHttpTransport"), patch(
            "extractor.sdk.Client"
        ) as client_cls:
            mock_client = AsyncMock()
            mock_client.call_tool = AsyncMock(side_effect=RuntimeError("boom"))
            client_cls.return_value = mock_client

            client = DocumentReaderClient()
            with pytest.raises(DocumentReaderToolError):
                await client.call_tool("scrape_webpage")
