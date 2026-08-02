# json-schema-binder

A lightweight, deterministic, and schema-aware variable binding and expression resolution library for JSON and Pydantic payloads.

## Features

- **Zero Heavy Dependencies**: Pure core depends only on `pydantic`, `jmespath`, and `jsonpath-ng`.
- **Multiple Engines**: Out-of-the-box support for **JMESPath**, **JSONPath**, and **Dot Notation**.
- **Dynamic Registry**: Easily register custom binding engines using the `@register_binding_engine` decorator.
- **Optional LLM Fallback Mapper**: Connect any LangChain `BaseChatModel` (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, `ChatOllama`) + Pydantic Schema for intelligent runtime argument repair.

## Installation

```bash
pip install json-schema-binder

# Optional: Install with LangChain LLM fallback support
pip install "json-schema-binder[llm]"
```

## Quick Start

### Basic Variable Binding

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
```

### LLM Fallback with LangChain Model

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from json_schema_binder import resolve_variables
from json_schema_binder.fallback import LLMFallbackMapper

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
fallback_mapper = LLMFallbackMapper(model=llm)

class TransferArgs(BaseModel):
    account_id: str = Field(description="Account identifier")
    amount: float = Field(description="Transfer amount")

result = resolve_variables(
    payload={"account_id": "$step_1.user.acc", "amount": "$step_1.missing_key"},
    context_store={"step_1": {"user": {"acc": "ACC-123"}, "total": 250.0}},
    engine="jmespath",
    target_schema=TransferArgs,
    fallback_mapper=fallback_mapper,
    directive="Extract total and map to amount"
)
```
