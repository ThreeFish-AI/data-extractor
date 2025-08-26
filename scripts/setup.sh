#!/bin/bash
# Setup script for Scrapy MCP Server with uv

set -e

echo "🚀 Setting up Scrapy MCP Server with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv found"

# Sync dependencies
echo "📦 Installing dependencies..."
uv sync

echo "🔧 Installing development dependencies..."
uv sync --extra dev

# Copy environment configuration if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "✏️  Please edit .env file to configure your settings"
else
    echo "ℹ️  .env file already exists"
fi

# Install playwright browsers if playwright is available
echo "🌐 Setting up browser dependencies..."
if uv run python -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright browsers..."
    uv run playwright install chromium
else
    echo "⚠️  Playwright not available, skipping browser installation"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run: uv run scrapy-mcp"
echo ""
echo "For development:"
echo "- Format code: uv run black scrapy_mcp/ examples/"
echo "- Run tests: uv run pytest"
echo "- Type check: uv run mypy scrapy_mcp/"