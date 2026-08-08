# 🛠️ AgentForge — Multi-step AI Agent Framework

A modular, provider-agnostic **Multi-step AI Agent Orchestration & Execution Framework**.

It enables complex multi-step agent pipelines by automatically generating execution plans, resolving step-to-step variable dependencies using pluggable expression engines (JMESPath, JSONPath, Dot Notation), and repairing payloads at runtime using LLM Fallback Mappers when deterministic binding falls short.

---

## 🏛️ Architecture Overview

```text
                               ┌──────────────────────────┐
                               │     User Query / Task    │
                               └────────────┬─────────────┘
                                            │
                                            ▼
                               ┌──────────────────────────┐
                               │   LLM Planner (LCEL)     │
                               │ Generates Pydantic Plan  │
                               └────────────┬─────────────┘
                                            │
                                            ▼
                               ┌──────────────────────────┐
                               │     HeadlessExecutor     │
                               └────────────┬─────────────┘
                                            │
                   ┌────────────────────────┴────────────────────────┐
                   │                                                 │
                   ▼                                                 ▼
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│  Pluggable Variable Binding Engine   │          │         LLM Fallback Mapper          │
│ (JMESPath / JSONPath / Dot Notation) │          │   (LangChain ChatModel + Pydantic)   │
└──────────────────┬───────────────────┘          └──────────────────┬───────────────────┘
                   │                                                 │
                   └────────────────────────┬────────────────────────┘
                                            │
                                            ▼
                               ┌──────────────────────────┐
                               │    MCP Client Session    │
                               │  (Streamable HTTP / STDIO│
                               └────────────┬─────────────┘
                                            │
                                            ▼
                               ┌──────────────────────────┐
                               │       MCP Server         │
                               └──────────────────────────┘
```

---

## ✨ Key Features

- **Pluggable Binding Engines**: Supports **JMESPath**, **JSONPath**, and **Dot Notation** registered via dynamic decorator factory (`@register_binding_engine`).
- **Execution Safety**: Implements strict `HALTED_BY_DESIGN` safeguards to halt execution safely if required step variables cannot be resolved.
- **Deeply Nested JSON Support**: Tested against 5-level nested enterprise JSON payloads (supply chain matrices, organizational structures).
- **MCP Protocol Native**: Built on `mcp.ClientSession` and FastMCP using Streamable HTTP transports.

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `>= 3.14`
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv)

### Installation

Clone the repository and install dependencies using `uv`:

```bash
git clone https://github.com/your-org/json-schema-transformer.git
cd json-schema-transformer
uv sync
```

### Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
# Optional additional providers:
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key
# OPENROUTER_API_KEY=your_openrouter_key
### Commands (Makefile)

Quick shortcuts via `make`:

```bash
make install        # Install dependencies via uv sync
make server         # Run standalone MCP Streamable HTTP server (src/mcp/server.py)
make agent          # Run interactive Planner & Execution Agent (src/core/main.py)
make test           # Run unit tests via pytest
make eval           # Run evaluation suite (jmespath)
make eval-jsonpath  # Run evaluation suite using jsonpath engine
make eval-dot       # Run evaluation suite using dot_notation engine
make clean          # Clean build artifacts and caches
```

### Running MCP Server and Agent as Independent Services

The MCP Server and the Agent CLI run as two completely decoupled services:

1. **Start the MCP Server** (Terminal 1):
   ```bash
   make server
   # or: uv run python -m src.mcp.server
   ```

2. **Run the Agent CLI or Evaluation Suite** (Terminal 2):
   ```bash
   make agent
   # or: uv run python -m src.core.main
   ```

---

## 📖 Usage Examples

### 1. Standalone Variable Binding

You can use the binding layer independently to extract and transform data between pipeline steps:

```python
from json_schema_binder import resolve_variables

context_store = {
    "step_1": {"products": [{"id": "P1", "name": "Laptop", "price": 1200}, {"id": "P2", "name": "Mouse", "price": 25}]}
}

# Resolve using JMESPath
payload = {"items": "$step_1.products[?price > `100`].name"}
resolved = resolve_variables(payload, context_store, engine="jmespath")
print(resolved)
# Output: {'items': ['Laptop']}

# Resolve using JSONPath
payload_jsonpath = {"items": "$step_1.products[?(@.price > 100)].name"}
resolved = resolve_variables(payload_jsonpath, context_store, engine="jsonpath")
print(resolved)
# Output: {'items': ['Laptop']}

# Resolve using Dot Notation
payload_dot = {"first_product": "$step_1.products.0.name"}
resolved = resolve_variables(payload_dot, context_store, engine="dot_notation")
print(resolved)
# Output: {'first_product': 'Laptop'}
```


### 3. Interactive CLI Execution

Launch the interactive CLI tool:

```bash
uv run python src/core/main.py
```

### 4. Running the Full Evaluation Benchmark

Run evaluation across all 11 test scenarios with CLI flags:

```bash
# Evaluate with JMESPath engine
uv run python scripts/evaluate_all.py --engine jmespath

# Run a specific test case (e.g., TC-01)
uv run python scripts/evaluate_all.py --tc TC-01
```

---

## 🧪 Testing

Run unit tests via `pytest`:

```bash
uv run pytest
```

Run complex 5-level nested end-to-end integration test over live MCP Server:

```bash
uv run python tests/test_real_complex_pipeline.py
```

---

## 📁 Repository Structure

```text
.
├── src/
│   ├── core/
│   │   ├── binding/             # Pluggable Binding Engines (JMESPath, JSONPath, Dot)
│   │   ├── engine/              # HeadlessExecutor, VariableParser, Protocols
│   │   ├── planner/             # LLM Planner & Structured Output Pydantic Models
│   │   ├── prompts/             # Prompt Templates (Planner)
│   │   ├── llm_client.py        # Centralized LangChain LLM Client Factory
│   │   ├── main.py              # Main CLI entrypoint
│   │   └── test_inputs.py       # Test Suite definition (TC-01..TC-11)
│   └── mcp/
│       ├── schema/              # Pydantic Schemas for MCP Tools
│       ├── tools/               # FastMCP Business Tools
│       └── server.py            # Streamable HTTP MCP Server
├── scripts/
│   └── evaluate_all.py          # Benchmark Evaluation Script
├── tests/                       # Unit & End-to-End Integration Tests
├── pyproject.toml               # Project Metadata & Dependencies
└── README.md                    # Project Documentation
```

---

## 📄 License

[MIT](LICENSE)
