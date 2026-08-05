import pytest
from unittest.mock import MagicMock
from src.agent.binder import (
    generate_schema,
    DynamicDataBinder as DynamicJMESPathBinder,
    DataMappingPath as JMESPathMapping,
    schemas_match
)

def test_generate_schema_primitives():
    assert generate_schema("hello") == {"type": "string"}
    assert generate_schema(123) == {"type": "integer"}
    assert generate_schema(45.67) == {"type": "number"}
    assert generate_schema(True) == {"type": "boolean"}
    assert generate_schema(None) == {"type": "null"}

def test_generate_schema_nested():
    data = {
        "products": [
            {"id": "p1", "name": "laptop"}
        ],
        "active": True
    }
    expected = {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"}
                    },
                    "required": ["id", "name"]
                }
            },
            "active": {"type": "boolean"}
        },
        "required": ["products", "active"]
    }
    assert generate_schema(data) == expected

def test_jmespath_binder_successful():
    # Mock LLM runner
    mock_runner = MagicMock()
    # The runner returns a JMESPathMapping instance
    mock_runner.return_value = JMESPathMapping(
        jmespath_expression="{query: search_products.items[0].name, limit: `5`}"
    )

    binder = DynamicJMESPathBinder(llm_runner=mock_runner)

    source_data = {
        "search_products": {
            "items": [{"name": "shoes", "price": 100}]
        }
    }
    target_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"}
        },
        "required": ["query"]
    }

    resolved = binder.bind(
        intent="Get the first product name as query, limit 5",
        source_data=source_data,
        target_schema=target_schema
    )

    assert resolved == {"query": "shoes", "limit": 5}
    mock_runner.assert_called_once()
    args, kwargs = mock_runner.call_args
    variables = args[0]
    assert variables["intent"] == "Get the first product name as query, limit 5"
    assert "search_products" in variables["source_schema"]
    assert "query" in variables["target_schema"]

def test_jmespath_binder_markdown_cleaning():
    mock_runner = MagicMock()
    # Mock return value wrapped in markdown codeblock
    mock_runner.return_value = JMESPathMapping(
        jmespath_expression="```jmespath\n{name: test.val}\n```"
    )

    binder = DynamicJMESPathBinder(llm_runner=mock_runner)
    source_data = {"test": {"val": "clean"}}
    resolved = binder.bind(
        intent="Map test value",
        source_data=source_data,
        target_schema={}
    )
    assert resolved == {"name": "clean"}

def test_schemas_match():
    # Simple structural match
    s1 = {"type": "object", "properties": {"a": {"type": "string"}}}
    s2 = {"type": "object", "properties": {"a": {"type": "string", "description": "some doc"}}}
    assert schemas_match(s1, s2) is True

    # Property mismatch
    s3 = {"type": "object", "properties": {"b": {"type": "string"}}}
    assert schemas_match(s1, s3) is False

    # Type mismatch
    s4 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    assert schemas_match(s1, s4) is False

    # Items matching
    s5 = {"type": "array", "items": {"type": "string"}}
    s6 = {"type": "array", "items": {"type": "string", "title": "hello"}}
    assert schemas_match(s5, s6) is True

def test_bind_with_fallback_success():
    # Pre-planned path should run without invoking LLM
    mock_runner = MagicMock()
    binder = DynamicJMESPathBinder(llm_runner=mock_runner)

    source_data = {"search_iphones": {"items": [{"name": "iPhone 15", "price": 800}]}}
    expected_schema = {
        "type": "object",
        "properties": {
            "search_iphones": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "integer"}
                            },
                            "required": ["name", "price"]
                        }
                    }
                },
                "required": ["items"]
            }
        },
        "required": ["search_iphones"]
    }

    # Pre-planned expression
    planned_expr = "{query: search_iphones.items[0].name}"

    resolved = binder.bind_with_fallback(
        intent="test intent",
        source_data=source_data,
        target_schema={},
        planned_jmespath=planned_expr,
        expected_source_schema=expected_schema
    )

    assert resolved == {"query": "iPhone 15"}
    mock_runner.assert_not_called()

def test_bind_with_fallback_schema_mismatch():
    # Schema mismatch should fall back to LLM mapping
    mock_runner = MagicMock()
    mock_runner.return_value = JMESPathMapping(
        jmespath_expression="{query: search_iphones.items[0].name}"
    )
    binder = DynamicJMESPathBinder(llm_runner=mock_runner)

    source_data = {"search_iphones": {"items": [{"name": "iPhone 15", "price": 800}]}}
    # Expected schema has mismatched type for price (string instead of integer)
    mismatched_expected = {
        "type": "object",
        "properties": {
            "search_iphones": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "string"}
                            },
                            "required": ["name", "price"]
                        }
                    }
                },
                "required": ["items"]
            }
        },
        "required": ["search_iphones"]
    }

    planned_expr = "{query: search_iphones.items[0].name}"

    resolved = binder.bind_with_fallback(
        intent="test intent",
        source_data=source_data,
        target_schema={},
        planned_jmespath=planned_expr,
        expected_source_schema=mismatched_expected
    )

    assert resolved == {"query": "iPhone 15"}
    mock_runner.assert_called_once()

def test_normalize_jmespath():
    from src.agent.binder import normalize_jmespath
    
    # Case 1: JSON double-quoted keys and double-quoted backticked string literal
    expr1 = '{"input":{"products":apply_discount.products,"target_currency":"`EUR`"}}'
    assert normalize_jmespath(expr1) == '{input:{products:apply_discount.products,target_currency: `"EUR"`}}'
    
    # Case 2: Number literal wrapped in quotes and backticks
    expr2 = '{"limit": "`5`"}'
    assert normalize_jmespath(expr2) == '{limit: `5`}'

    # Case 3: Boolean literal wrapped in quotes and backticks
    expr3 = '{"active": "`true`"}'
    assert normalize_jmespath(expr3) == '{active: `true`}'

    # Case 4: Nested JSON literal (keys inside backticks must not be stripped of quotes)
    expr4 = '{"input": `{"network_name": "GlobalSupplyNet", "version": 1.0}`}'
    assert normalize_jmespath(expr4) == '{input: `{"network_name": "GlobalSupplyNet", "version": 1.0}`}'
    
    # Case 5: Entire expression is a JSON literal
    expr5 = '`{"input": {"network_name": "Global"}}`'
    assert normalize_jmespath(expr5) == '`{"input": {"network_name": "Global"}}`'

    # Case 6: Unclosed backtick at the end of the expression
    expr6 = '`{"input": {"network_name": "Global"}}'
    assert normalize_jmespath(expr6) == '`{"input": {"network_name": "Global"}}`'


