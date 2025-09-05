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

# Copy environment configuration
cp .env.example .env
```

### Running the Server

```bash
# Start the MCP server (primary command)
uv run data-extractor

# Alternative: Run as Python module
uv run python -m extractor.server

# Run with environment variables
uv run --env SCRAPY_MCP_ENABLE_JAVASCRIPT=true data-extractor
```

### Code Quality and Testing

```bash
# Format code with Black
uv run black extractor/ examples/

# Lint with flake8
uv run flake8 extractor/

# Type checking with mypy
uv run mypy extractor/

# Run tests
uv run pytest

# Add dependencies
uv add <package-name>
uv add --dev <package-name>

# Update dependencies
uv lock --upgrade
```

## Architecture Overview

### Core Module Structure

The system is built with a layered architecture centered around method auto-selection and enterprise-grade utilities:

**extractor/server.py** - FastMCP server with 10 MCP tools using `@app.tool()` decorators. Each tool follows a pattern: Pydantic request models → method selection → error handling → metrics collection.

**extractor/scraper.py** - Multi-strategy scraping engine with automatic method selection:

- `WebScraper.scrape_url()` orchestrates method selection based on requirements
- Supports Simple HTTP, Scrapy framework, Selenium browser automation
- Method selection logic considers JavaScript detection and anti-bot protection needs

**extractor/advanced_features.py** - Stealth capabilities and form automation:

- `AntiDetectionScraper` using undetected-chromedriver and Playwright
- `FormHandler` for complex form interactions (dropdowns, checkboxes, file uploads)

**extractor/utils.py** - Enterprise utilities with async support:

- `RateLimiter`, `RetryManager`, `CacheManager`, `MetricsCollector`, `ErrorHandler`
- All utilities follow patterns for async support, error handling, and metrics

**extractor/config.py** - Pydantic BaseSettings with automatic environment variable mapping using `SCRAPY_MCP_` prefix.

### Key Design Patterns

**Method Auto-Selection**: `WebScraper` intelligently chooses scraping methods based on JavaScript requirements, anti-bot protection, and performance needs.

**Layered Error Handling**: Errors are caught at multiple levels, categorized (timeout, connection, anti-bot), and handled with appropriate retry strategies.

**Enterprise Features**: Built-in rate limiting, caching with TTL, comprehensive metrics collection, and proxy support for production deployment.

## Configuration System

Environment variables use `SCRAPY_MCP_` prefix (see .env.example):

**Critical Settings:**

- `SCRAPY_MCP_ENABLE_JAVASCRIPT` - Enables browser automation globally
- `SCRAPY_MCP_USE_RANDOM_USER_AGENT` - Anti-detection feature
- `SCRAPY_CONCURRENT_REQUESTS` - Controls Scrapy concurrency
- `SCRAPY_MCP_BROWSER_TIMEOUT` - Browser wait timeout

## Data Extraction Configuration

Flexible extraction configs support simple CSS selectors and complex attribute extraction:

- Simple: `{"title": "h1"}`
- Complex: `{"products": {"selector": ".product", "multiple": true, "attr": "text"}}`
- Attributes: text content, href links, src images, custom attributes

See `examples/extraction_configs.py` for comprehensive examples covering e-commerce, news, job listings, and real estate scenarios.

## Working with the Codebase

**Adding New MCP Tools**: Add to `server.py` using `@app.tool()` decorator. Follow existing pattern: Pydantic request model → error handling → metrics collection.

**Extending Scraping Methods**: Modify `scraper.py` classes. The `WebScraper.scrape_url()` method orchestrates method selection logic.

**Adding Anti-Detection Features**: Extend `AntiDetectionScraper` in `advanced_features.py`. Consider browser stealth options, behavior simulation, and proxy rotation.

**Configuration Changes**: Add settings to `ScrapyMCPSettings` in `config.py` using Pydantic Field with environment variable mapping.

**Utility Functions**: Add to `utils.py` following existing patterns for async support, error handling, and metrics integration.

## Performance Considerations

- Server uses asyncio for concurrent operations
- Scrapy runs on Twisted reactor (single-threaded event loop)
- Browser automation (Selenium/Playwright) is resource-intensive
- Caching significantly improves repeated request performance
- Rate limiting prevents overwhelming target servers

## Browser Dependencies

Requires Chrome/Chromium browser for Selenium and stealth features. Playwright downloads its own browser binaries automatically.

## Security Notes

- Stealth features should be used ethically
- Always check robots.txt using provided tool
- Proxy support available but ensure HTTPS proxies
- No sensitive data logging - handle credentials carefully
