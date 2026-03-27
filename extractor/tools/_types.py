"""工具层共享类型别名。"""

from typing import Literal

ScrapeMethod = Literal["auto", "simple", "scrapy", "selenium"]
BrowserMethod = Literal["selenium", "playwright"]
PDFMethod = Literal["auto", "pymupdf", "pypdf", "docling", "smart"]
PDFOutputFormat = Literal["markdown", "text"]
StructuredDataType = Literal[
    "all", "contact", "social", "content", "products", "addresses"
]
