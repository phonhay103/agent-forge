# json-schema-binder

A lightweight, deterministic, strongly-typed, and schema-aware variable binding and expression resolution library for JSON, Pydantic, and Python dataclass payloads.

## Features

- **Zero Heavy Dependencies**: Pure core depends only on `pydantic`, `jmespath`, and `jsonpath-ng`.
- **Strongly Typed Core**: Built with standard Pydantic models (`BindingContext`, `BindingResult[T]`, `BindingRequest[T]`) eliminating loose untyped dictionary signatures.
- **Multiple Engines**: Out-of-the-box support for **JMESPath**, **JSONPath**, and **Dot Notation**.
- **Rich Type Support**: Seamlessly processes Pydantic `BaseModel`, Python `dataclass`, dicts, lists, strings, and primitives while preserving target type `T`.
- **Dual-Mode Context Resolution**: Supports both **Keyed Context Mode** (`$var.path`) and **Root Context Evaluation Mode** (querying context root directly).
- **Dynamic Registry**: Easily register custom binding engines using the `@register_binding_engine` decorator.

## Installation

```bash
pip install json-schema-binder
```

## Quick Start

### Basic Variable Binding with `BindingResult[T]`

```python
from json_schema_binder import resolve_variables, BindingContext

context = {
    "source": {
        "products": [
            {"id": "P1", "name": "Laptop", "price": 1200},
            {"id": "P2", "name": "Mouse", "price": 25}
        ]
    }
}

# Resolve using JMESPath
payload = {"items": "$source.products[?price > `100`].name"}
result = resolve_variables(payload, context, engine="jmespath")

print(result.resolved_payload)
# Output: {'items': ['Laptop']}
print(result.is_fully_resolved)
# Output: True
```

