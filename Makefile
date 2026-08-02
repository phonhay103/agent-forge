export PYTHONPATH := .

.PHONY: help install test eval eval-fallback eval-jsonpath eval-dot server agent clean

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

agent: ## Run the interactive LLM Planner & Execution Agent
	uv run python -m src.core.main

test: ## Run unit tests with pytest
	uv run pytest

eval: ## Run evaluation suite with default engine (jmespath)
	uv run python scripts/evaluate_all.py

eval-fallback: ## Run evaluation suite with LLM fallback enabled
	uv run python scripts/evaluate_all.py --fallback

eval-jsonpath: ## Run evaluation suite using jsonpath engine
	uv run python scripts/evaluate_all.py --engine jsonpath

eval-dot: ## Run evaluation suite using dot_notation engine
	uv run python scripts/evaluate_all.py --engine dot_notation

clean: ## Clean cache files and build artifacts
	rm -rf .pytest_cache .venv __pycache__ evaluation_report.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
