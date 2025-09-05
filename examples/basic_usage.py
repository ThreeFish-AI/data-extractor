#!/usr/bin/env python3
"""
Basic usage examples for the Data Extractor MCP Server.

This script demonstrates how to use various scraping tools programmatically.
Note: This is for demonstration purposes. In real usage, the MCP server
would be called through MCP client tools like Claude Desktop.
"""

import asyncio
import json
from typing import Dict, Any


# Mock MCP client calls - replace with actual MCP client in production
async def mock_mcp_call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Mock MCP tool call - replace with actual MCP client."""
    print(f"Mock call to {tool_name} with params: {json.dumps(params, indent=2)}")

    # This would normally be handled by the MCP client
    # Return mock successful response
    return {
        "success": True,
        "data": {"message": f"Mock response from {tool_name}"},
        "duration_ms": 1000,
    }


async def example_basic_scraping():
    """Example: Basic webpage scraping."""
    print("=== Basic Webpage Scraping ===")

    params = {"url": "https://httpbin.org/html", "method": "simple"}

    result = await mock_mcp_call("scrape_webpage", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_advanced_extraction():
    """Example: Advanced data extraction with configuration."""
    print("=== Advanced Data Extraction ===")

    params = {
        "url": "https://example.com",
        "method": "auto",
        "extract_config": {
            "title": "h1",
            "paragraphs": {"selector": "p", "multiple": True, "attr": "text"},
            "links": {"selector": "a", "multiple": True, "attr": "href"},
            "meta_description": {
                "selector": "meta[name='description']",
                "attr": "content",
                "multiple": False,
            },
        },
    }

    result = await mock_mcp_call("scrape_webpage", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_multiple_urls():
    """Example: Scraping multiple URLs concurrently."""
    print("=== Multiple URL Scraping ===")

    params = {
        "urls": [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
        ],
        "method": "simple",
        "extract_config": {"title": "title", "headings": "h1, h2, h3"},
    }

    result = await mock_mcp_call("scrape_multiple_webpages", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_stealth_scraping():
    """Example: Stealth scraping for protected websites."""
    print("=== Stealth Scraping ===")

    params = {
        "url": "https://example.com",
        "method": "selenium",
        "scroll_page": True,
        "wait_for_element": "body",
        "extract_config": {"content": {"selector": "body", "attr": "text"}},
    }

    result = await mock_mcp_call("scrape_with_stealth", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_form_interaction():
    """Example: Form filling and submission."""
    print("=== Form Interaction ===")

    params = {
        "url": "https://httpbin.org/forms/post",
        "form_data": {
            "input[name='custname']": "John Doe",
            "input[name='custtel']": "1234567890",
            "input[name='custemail']": "john@example.com",
            "select[name='size']": "large",
        },
        "submit": False,  # Don't actually submit for demo
        "method": "selenium",
    }

    result = await mock_mcp_call("fill_and_submit_form", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_link_extraction():
    """Example: Extracting links from a webpage."""
    print("=== Link Extraction ===")

    params = {
        "url": "https://example.com",
        "internal_only": False,
        "filter_domains": None,
        "exclude_domains": ["spam.com", "ads.com"],
    }

    result = await mock_mcp_call("extract_links", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_structured_data_extraction():
    """Example: Extracting structured data."""
    print("=== Structured Data Extraction ===")

    params = {
        "url": "https://example.com/contact",
        "data_type": "all",  # Extract all types of structured data
    }

    result = await mock_mcp_call("extract_structured_data", params)
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_page_info():
    """Example: Getting basic page information."""
    print("=== Page Information ===")

    result = await mock_mcp_call("get_page_info", {"url": "https://example.com"})
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_robots_check():
    """Example: Checking robots.txt."""
    print("=== Robots.txt Check ===")

    result = await mock_mcp_call("check_robots_txt", {"url": "https://example.com"})
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def example_server_metrics():
    """Example: Getting server metrics."""
    print("=== Server Metrics ===")

    result = await mock_mcp_call("get_server_metrics", {})
    print(f"Result: {json.dumps(result, indent=2)}")
    print()


async def main():
    """Run all examples."""
    print("🚀 Data Extractor MCP Server Usage Examples")
    print("=" * 50)
    print()

    examples = [
        example_basic_scraping,
        example_advanced_extraction,
        example_multiple_urls,
        example_stealth_scraping,
        example_form_interaction,
        example_link_extraction,
        example_structured_data_extraction,
        example_page_info,
        example_robots_check,
        example_server_metrics,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")

        # Wait between examples
        await asyncio.sleep(1)

    print("✅ All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
