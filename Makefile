export PYTHONPATH := .

.PHONY: help install test eval eval-jsonpath eval-dot server agent clean lint format

# Default target
.DEFAULT_GOAL := help

help: ## Display available commands
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv sync
	uv sync

server: ## Run the standalone MCP Streamable HTTP server (http://127.0.0.1:8000/mcp)
	uv run python -m src.mcp.server

agent: ## Run the interactive Multi-Agent System
	uv run python -m src.main

agent-static: ## Run Static Binding Agent directly
	uv run python -c "import asyncio; from src.agent.main import main_static; asyncio.run(main_static())"

agent-dynamic: ## Run Dynamic Binding Agent directly
	uv run python -c "import asyncio; from src.agent.main import main_dynamic; asyncio.run(main_dynamic())"

agent-abstract: ## Run Abstract Planning Agent directly
	uv run python -m src.abstract_agent

lint: ## Run lint checks with Ruff (with auto-fix) and ty on the repository
	uv run ruff check --fix .
	uv run ty check

format: ## Format code using Ruff formatter on the repository
	uv run ruff format .

test: ## Run all unit tests with pytest
	PYTHONPATH=. uv run pytest tests/
	cd packages/prompt_composer && uv run pytest tests/

eval: ## Run evaluation suite with default engine (jmespath)
	uv run python scripts/evaluate_all.py

eval-jsonpath: ## Run evaluation suite using jsonpath engine
	uv run python scripts/evaluate_all.py --engine jsonpath

eval-dot: ## Run evaluation suite using dot_notation engine
	uv run python scripts/evaluate_all.py --engine dot_notation

clean: ## Clean cache files and build artifacts
	rm -rf .pytest_cache .venv __pycache__ evaluation_report.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
