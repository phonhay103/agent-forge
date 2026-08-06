default:
    @just --list

# Install dependencies using uv sync
install:
    uv sync

# Run standalone MCP Streamable HTTP server
server:
    uv run python -m src.mcp.server

# Run the interactive Multi-Agent System
agent:
    uv run python -m src.main

# Run Static Binding Agent directly
agent-static:
    uv run python -c "import asyncio; from src.agent.main import main_static; asyncio.run(main_static())"

# Run Dynamic Binding Agent directly
agent-dynamic:
    uv run python -c "import asyncio; from src.agent.main import main_dynamic; asyncio.run(main_dynamic())"

# Run Abstract Planning Agent directly
agent-abstract:
    uv run python -m src.abstract_agent

# Run lint checks with Ruff (with auto-fix) and MyPy on the rendering engine
lint:
    uv run ruff check --fix packages/prompt_composer/src/prompt_composer/renderers/
    uv run mypy packages/prompt_composer/src/prompt_composer/renderers/

# Format code using Ruff formatter on the rendering engine
format:
    uv run ruff format packages/prompt_composer/src/prompt_composer/renderers/

# Run all unit tests with pytest
test:
    PYTHONPATH=. uv run pytest tests/
    cd packages/prompt_composer && uv run pytest tests/

# Run evaluation suite with default engine (jmespath)
eval:
    uv run python scripts/evaluate_all.py

# Run evaluation suite using jsonpath engine
eval-jsonpath:
    uv run python scripts/evaluate_all.py --engine jsonpath

# Run evaluation suite using dot_notation engine
eval-dot:
    uv run python scripts/evaluate_all.py --engine dot_notation

# Clean cache files and build artifacts
clean:
    rm -rf .pytest_cache .venv __pycache__ evaluation_report.json
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
