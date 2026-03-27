"""Python SDK facade for the document-reader MCP service."""

from __future__ import annotations

from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class DocumentReaderError(Exception):
    """Base exception for Python SDK failures."""


class DocumentReaderConnectionError(DocumentReaderError):
    """Raised when the SDK cannot establish or maintain a client session."""


class DocumentReaderToolError(DocumentReaderError):
    """Raised when a tool invocation fails."""


class DocumentReaderClient:
    """High-level async SDK for calling the document-reader MCP service."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8081/mcp",
        *,
        headers: dict[str, str] | None = None,
        auth: Any = None,
        timeout: float | int | None = None,
        client_name: str = "document-reader-sdk",
    ) -> None:
        self.base_url = base_url
        self._transport = StreamableHttpTransport(
            url=base_url,
            headers=headers,
            auth=auth,
        )
        self._client = Client(
            self._transport,
            name=client_name,
            timeout=timeout,
        )
        self._connected = False

    async def __aenter__(self) -> "DocumentReaderClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> None:
        """Connect to the remote MCP service."""
        if self._connected:
            return
        try:
            await self._client.__aenter__()
            self._connected = True
        except Exception as exc:  # pragma: no cover - delegated to FastMCP
            raise DocumentReaderConnectionError(
                f"Failed to connect to document-reader service at {self.base_url}"
            ) from exc

    async def close(self) -> None:
        """Close the underlying FastMCP client."""
        if not self._connected:
            return
        try:
            await self._client.__aexit__(None, None, None)
        finally:
            self._connected = False

    async def list_tools(self) -> list[Any]:
        """List server tools after ensuring the client session is active."""
        await self.connect()
        try:
            return await self._client.list_tools()
        except Exception as exc:  # pragma: no cover - delegated to FastMCP
            raise DocumentReaderConnectionError(
                "Failed to list tools from document-reader service"
            ) from exc

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float | int | None = None,
        raise_on_error: bool = True,
        meta: dict[str, Any] | None = None,
    ) -> Any:
        """Call an arbitrary MCP tool through the project SDK."""
        await self.connect()
        try:
            return await self._client.call_tool(
                name,
                arguments or {},
                timeout=timeout,
                raise_on_error=raise_on_error,
                meta=meta,
            )
        except Exception as exc:  # pragma: no cover - delegated to FastMCP
            raise DocumentReaderToolError(
                f"Tool '{name}' failed on document-reader service"
            ) from exc

    async def scrape_webpage(
        self,
        *,
        url: str,
        method: str = "auto",
        extract_config: dict[str, Any] | None = None,
        wait_for_element: str | None = None,
    ) -> Any:
        """Typed convenience wrapper for scrape_webpage."""
        return await self.call_tool(
            "scrape_webpage",
            {
                "url": url,
                "method": method,
                "extract_config": extract_config,
                "wait_for_element": wait_for_element,
            },
        )

    async def convert_webpage_to_markdown(
        self,
        *,
        url: str,
        method: str = "auto",
        extract_main_content: bool = True,
        embed_images: bool = False,
    ) -> Any:
        """Typed convenience wrapper for convert_webpage_to_markdown."""
        return await self.call_tool(
            "convert_webpage_to_markdown",
            {
                "url": url,
                "method": method,
                "extract_main_content": extract_main_content,
                "embed_images": embed_images,
            },
        )
