# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive web scraping MCP (Model Context Protocol) server built on FastMCP and Scrapy, designed for enterprise-grade web scraping with anti-detection capabilities. The server provides 10 MCP tools for various scraping scenarios, from simple HTTP requests to sophisticated stealth scraping and form automation.

## Development Commands

### Setup and Installation

```bash
# Quick setup using provided script (recommended)
./scripts/setup.sh

# Manual setup with uv
uv sync

# Install with development dependencies
uv sync --extra dev

# Alternative: Install package in development mode
uv pip install -e .

# Copy environment configuration
cp .env.example .env
```

### Running the Server

```bash
# Start the MCP server
scrapy-mcp

# Run using uv
uv run scrapy-mcp

# Or run directly with Python using uv
uv run python -m scrapy_mcp.server

# Run with custom configuration
SCRAPY_MCP_ENABLE_JAVASCRIPT=true scrapy-mcp

# Run with environment variables using uv
uv run --env SCRAPY_MCP_ENABLE_JAVASCRIPT=true scrapy-mcp
```

### Code Quality and Testing

```bash
# Format code with Black (using uv)
uv run black scrapy_mcp/ examples/

# Lint with flake8 (using uv)
uv run flake8 scrapy_mcp/

# Type checking with mypy (using uv)
uv run mypy scrapy_mcp/

# Run tests (when available)
uv run pytest

# Run async tests specifically
uv run pytest -m asyncio

# Add new dependencies
uv add <package-name>

# Add development dependencies
uv add --dev <package-name>

# Update dependencies
uv lock --upgrade
```

## Architecture Overview

### Core Components

**scrapy_mcp/server.py** - Main FastMCP server with 10 MCP tools:

- `scrape_webpage` - Basic scraping with method auto-selection
- `scrape_multiple_webpages` - Concurrent multi-URL scraping
- `scrape_with_stealth` - Anti-detection scraping using undetected browsers
- `fill_and_submit_form` - Form automation with Selenium/Playwright
- `extract_links` - Specialized link extraction with filtering
- `extract_structured_data` - Automatic detection of contact info, social links
- `get_page_info` - Quick page metadata retrieval
- `check_robots_txt` - Ethical scraping compliance checker
- `get_server_metrics` - Performance monitoring and statistics
- `clear_cache` - Cache management

**scrapy_mcp/scraper.py** - Core scraping engine with multiple strategies:

- `SimpleScraper` - Fast HTTP requests with BeautifulSoup
- `ScrapyWrapper` - Scrapy framework integration for large-scale scraping
- `SeleniumScraper` - Browser automation for JavaScript-heavy sites
- `WebScraper` - Main orchestrator that auto-selects appropriate method

**scrapy_mcp/advanced_features.py** - Anti-detection and form handling:

- `AntiDetectionScraper` - Stealth techniques using undetected-chromedriver and Playwright
- `FormHandler` - Handles various form elements (text, dropdowns, checkboxes, file uploads)

**scrapy_mcp/utils.py** - Enterprise utilities:

- `RateLimiter` - Request throttling to prevent server overload
- `RetryManager` - Exponential backoff retry logic
- `CacheManager` - In-memory caching with TTL
- `MetricsCollector` - Performance tracking and statistics
- `ErrorHandler` - Centralized error categorization and handling

**scrapy_mcp/config.py** - Configuration management using Pydantic BaseSettings with environment variable support for all aspects (concurrency, delays, browser settings, proxy configuration).

### Key Design Patterns

**Method Auto-Selection**: The `WebScraper` class intelligently chooses between simple HTTP, Scrapy, Selenium, or stealth methods based on requirements (JavaScript detection, anti-bot protection needs).

**Layered Error Handling**: Errors are caught at multiple levels, categorized (timeout, connection, anti-bot, etc.), and handled with appropriate retry strategies.

**Enterprise Features**: Built-in rate limiting, caching, metrics collection, and proxy support for production deployment.

## Configuration System

The server uses environment variables for configuration (see .env.example):

**Critical Settings:**

- `SCRAPY_MCP_ENABLE_JAVASCRIPT` - Enables browser automation globally
- `SCRAPY_MCP_USE_RANDOM_USER_AGENT` - Anti-detection feature
- `SCRAPY_CONCURRENT_REQUESTS` - Controls Scrapy concurrency
- `SCRAPY_MCP_BROWSER_TIMEOUT` - Browser wait timeout

## Data Extraction Configuration

The system uses flexible extraction configs that support:

- Simple CSS selectors: `{"title": "h1"}`
- Complex configurations: `{"products": {"selector": ".product", "multiple": true, "attr": "text"}}`
- Attribute extraction: text content, href links, src images, custom attributes

See `examples/extraction_configs.py` for comprehensive examples covering e-commerce, news, job listings, real estate, and other common scenarios.

## Working with the Codebase

**Adding New MCP Tools**: Add to `server.py` using the `@app.tool()` decorator. Follow the pattern of existing tools with Pydantic request models, error handling, and metrics collection.

**Extending Scraping Methods**: Modify `scraper.py` classes. The `WebScraper.scrape_url()` method orchestrates method selection.

**Adding Anti-Detection Features**: Extend `AntiDetectionScraper` in `advanced_features.py`. Consider browser stealth options, behavior simulation, and proxy rotation.

**Configuration Changes**: Add new settings to `ScrapyMCPSettings` in `config.py`. Use Pydantic Field with env variable mapping.

**Utility Functions**: Add reusable utilities to `utils.py`. Follow existing patterns for async support, error handling, and metrics.

## Browser Dependencies

The project requires Chrome/Chromium browser for Selenium and stealth features. Playwright downloads its own browser binaries. Consider these when deploying or containerizing.

## Performance Considerations

- The server uses asyncio for concurrent operations
- Scrapy runs on Twisted reactor (single-threaded event loop)
- Browser automation (Selenium/Playwright) is resource-intensive
- Caching significantly improves repeated request performance
- Rate limiting prevents overwhelming target servers

## Security Notes

- Stealth features help avoid detection but should be used ethically
- Always check robots.txt using the provided tool
- Proxy support available but ensure HTTPS proxies for security
- No sensitive data logging - credentials should be handled carefully
