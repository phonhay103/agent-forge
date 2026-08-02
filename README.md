# JSON Schema Transformer & MCP Headless Core

A modular, provider-agnostic **MCP (Model Context Protocol) Headless Execution Engine & Schema Transformer**.

It enables multi-step tool-calling pipelines by automatically generating execution plans, resolving step-to-step variable dependencies using pluggable expression engines (JMESPath, JSONPath, Dot Notation), and repairing payloads at runtime using LLM Fallback Mappers when deterministic binding falls short.

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

- **Decoupled Architecture**: Zero concrete library coupling between business logic, transport layers, and LLM providers.
- **Pluggable Binding Engines**: Supports **JMESPath**, **JSONPath**, and **Dot Notation** registered via dynamic decorator factory (`@register_binding_engine`).
- **Flexible LLM Fallback**: Accepts **any general LangChain ChatModel instance** (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, `ChatOllama`, `ChatOpenRouter`) combined with Pydantic or JSON Schema for runtime payload repair.
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
```

---

## 📖 Usage Examples

### 1. Standalone Variable Binding

You can use the binding layer independently to extract and transform data between pipeline steps:

```python
from json_schema_binder import resolve_variables

context_store = {
    "step_1": {
        "products": [
            {"id": "P1", "name": "Laptop", "price": 1200},
            {"id": "P2", "name": "Mouse", "price": 25}
        ]
    }
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

### 2. Standalone LLM Fallback with LangChain Models

Pass any standard LangChain ChatModel instance into `LLMFallbackMapper`:

```python
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from json_schema_binder import resolve_variables
from json_schema_binder.fallback import LLMFallbackMapper

# 1. Instantiate any LangChain ChatModel
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
fallback_mapper = LLMFallbackMapper(model=llm)

# 2. Define target schema as Pydantic or Dict
class ConvertCurrencyInput(BaseModel):
    amount: float = Field(description="Amount to convert")
    from_currency: str = Field(description="Source currency code")
    to_currency: str = Field(description="Target currency code")

context = {
    "step_1": {
        "total_inventory_value": 5000.0
    }
}

# 3. Resolve with automatic LLM Fallback repair if key is missing
result = resolve_variables(
    payload={"amount": "$step_1.missing_key", "from_currency": "USD", "to_currency": "EUR"},
    context_store=context,
    engine="jmespath",
    target_schema=ConvertCurrencyInput,
    fallback_mapper=fallback_mapper,
    directive="Extract total_inventory_value and map to amount"
)

print(result)
# Output: {'amount': 5000.0, 'from_currency': 'USD', 'to_currency': 'EUR'}
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

# Evaluate with Automatic LLM Fallback enabled
uv run python scripts/evaluate_all.py --engine jmespath --fallback

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
│   │   ├── binding/             # Pluggable Binding Engines (JMESPath, JSONPath, Dot) & Fallback
│   │   ├── engine/              # HeadlessExecutor, VariableParser, Protocols
│   │   ├── planner/             # LLM Planner & Structured Output Pydantic Models
│   │   ├── prompts/             # Prompt Templates (Planner, Fallback)
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
