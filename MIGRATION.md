# Migration Guide: pip to uv

This guide helps you migrate from pip-based package management to uv for the Scrapy MCP Server.

## What Changed

### Removed Files
- `requirements.txt` - Replaced by dependencies in `pyproject.toml`

### New Files
- `.python-version` - Specifies Python version for uv
- `scripts/setup.sh` - Automated setup script
- `uv.lock` - Lock file (will be created by uv)

### Updated Files
- `pyproject.toml` - Enhanced with uv configuration and missing dependencies
- `README.md` - Updated installation instructions
- `CLAUDE.md` - Updated development commands
- `CHANGELOG.md` - Documented migration

## Why uv?

uv provides several advantages over pip:

- **Speed**: 10-100x faster dependency resolution and installation
- **Better dependency resolution**: More reliable and deterministic
- **Lock files**: Reproducible builds across environments
- **Modern Python tooling**: Built in Rust with excellent performance
- **Backward compatibility**: Works with existing pyproject.toml files

## Migration Steps

### For New Setup

If you're setting up the project fresh:

```bash
git clone <repository-url>
cd scrapy-mcp
./scripts/setup.sh
```

### For Existing Development Environment

If you already have the project set up with pip:

```bash
# 1. Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Remove old virtual environment (optional but recommended)
deactivate  # if you're in a virtual environment
rm -rf venv/  # or whatever your virtual environment is called

# 3. Use uv to create new environment and install dependencies
uv sync --extra dev

# 4. Activate the new uv environment
source .venv/bin/activate  # uv creates .venv by default

# 5. Test that everything works
uv run scrapy-mcp --help
```

## New Commands

Replace your old pip commands with these uv equivalents:

### Development Commands

| Old (pip) | New (uv) |
|-----------|----------|
| `pip install -e .` | `uv sync` |
| `pip install -e ".[dev]"` | `uv sync --extra dev` |
| `python -m scrapy_mcp.server` | `uv run scrapy-mcp` |
| `black scrapy_mcp/` | `uv run black scrapy_mcp/` |
| `pytest` | `uv run pytest` |
| `mypy scrapy_mcp/` | `uv run mypy scrapy_mcp/` |

### Dependency Management

| Task | uv Command |
|------|------------|
| Add new dependency | `uv add package-name` |
| Add dev dependency | `uv add --dev package-name` |
| Update dependencies | `uv lock --upgrade` |
| Install from lock | `uv sync` |

## Environment Management

uv automatically manages virtual environments:

- Creates `.venv/` directory in project root
- Activates automatically when using `uv run`
- No need to manually create or activate environments

## Lock File Benefits

The `uv.lock` file provides:

- **Reproducible builds**: Exact same versions across all environments
- **Security**: Cryptographic hashes for all packages
- **Performance**: Faster installs from cached resolution

**Important**: Always commit `uv.lock` to version control.

## CI/CD Updates

If you have CI/CD pipelines, update them:

```yaml
# Old
- run: pip install -e ".[dev]"

# New  
- run: uv sync --extra dev
```

For GitHub Actions, consider using the official uv action:

```yaml
- uses: astral-sh/setup-uv@v1
- run: uv sync --extra dev
```

## Troubleshooting

### "uv not found"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not resolving

Try clearing uv cache:
```bash
uv cache clean
uv sync --extra dev
```

### Import errors

Make sure you're using uv run:
```bash
uv run python -c "import scrapy_mcp"
```

### Legacy pip compatibility

uv provides pip compatibility:
```bash
uv pip install package-name
uv pip freeze
uv pip list
```

## Rollback (if needed)

If you need to rollback to pip:

```bash
# Recreate requirements.txt
uv pip freeze > requirements.txt

# Use traditional pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Benefits After Migration

After migrating to uv, you'll experience:

- **Faster installs**: Dependency resolution and installation is much faster
- **Better reproducibility**: Lock files ensure consistent environments
- **Simplified workflow**: One tool for all package management needs
- **Better error messages**: More helpful debugging information
- **Modern tooling**: Built with latest Python packaging standards

## Support

For uv-specific issues, check:
- [uv documentation](https://github.com/astral-sh/uv)
- [uv GitHub repository](https://github.com/astral-sh/uv/issues)

For project-specific issues, continue using the project's issue tracker.