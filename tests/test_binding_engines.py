from json_schema_binder import (
    get_binding_engine,
    BindingType,
    JMESPathBindingEngine,
    JSONPathBindingEngine,
    DotNotationBindingEngine,
    LLMFallbackMapper
)
from src.mcp.schema.models import SupplyChainOutput, RegionSummary, BlockSummary


def test_factory_creation():
    jmes_engine = get_binding_engine("jmespath")
    assert isinstance(jmes_engine, JMESPathBindingEngine)
    assert jmes_engine.binding_type == BindingType.JMESPATH

    jsonpath_engine = get_binding_engine("jsonpath")
    assert isinstance(jsonpath_engine, JSONPathBindingEngine)
    assert jsonpath_engine.binding_type == BindingType.JSONPATH

    dot_engine = get_binding_engine("dot_notation")
    assert isinstance(dot_engine, DotNotationBindingEngine)
    assert dot_engine.binding_type == BindingType.DOT_NOTATION


def test_jmespath_binding_engine():
    engine = JMESPathBindingEngine()
    context = {
        "step_1": {
            "products": [
                {"name": "Laptop", "price": 1200},
                {"name": "Mouse", "price": 25}
            ]
        }
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: JMESPath" in instruction

    res = engine.resolve("$step_1.products[?price > `100`].name", context)
    assert res == ["Laptop"]


def test_jsonpath_binding_engine():
    engine = JSONPathBindingEngine()
    context = {
        "step_1": {
            "products": [
                {"name": "Laptop", "price": 1200},
                {"name": "Mouse", "price": 25}
            ]
        }
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: JSONPath" in instruction

    res = engine.resolve("$step_1.products[?(@.price > 100)].name", context)
    assert res == ["Laptop"]

    res_single = engine.resolve("$step_1.products[0].name", context)
    assert res_single == "Laptop"


def test_dot_notation_binding_engine():
    engine = DotNotationBindingEngine()
    context = {
        "step_1": {
            "products": [
                {"name": "Laptop", "price": 1200},
                {"name": "Mouse", "price": 25}
            ]
        }
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: Dot Notation" in instruction

    res = engine.resolve("$step_1.products.0.name", context)
    assert res == "Laptop"


import os

def test_llm_fallback_direct_mapping():
    if not os.getenv("GOOGLE_API_KEY"):
        print("Skipping LLM Fallback test because GOOGLE_API_KEY is not set.")
        return
    from src.core.llm_client import get_llm_client
    mapper = LLMFallbackMapper(model=get_llm_client())
    context_data = {
        "total_inventory_value": 5000.0,
        "low_stock_skus": ["SKU-100", "SKU-200"]
    }
    target_tool_input_schema = {
        "title": "ConvertCurrencyInput",
        "properties": {
            "amount": {"type": "number"},
            "from_currency": {"type": "string"},
            "to_currency": {"type": "string"}
        }
    }

    # Test repair_payload fallback mapping
    mapped = mapper.repair_payload(
        context_store={"step_1": context_data},
        target_schema=target_tool_input_schema,
        partially_resolved_payload={"amount": "$step_1.non_existent_key", "from_currency": "USD"},
        directive="Extract total_inventory_value and map to amount"
    )
    assert mapped is not None
    assert mapped.get("amount") == 5000.0
    assert mapped.get("from_currency") == "USD"


def test_jmespath_automatic_llm_fallback():
    if not os.getenv("GOOGLE_API_KEY"):
        print("Skipping JMESPath LLM Fallback test because GOOGLE_API_KEY is not set.")
        return
    engine = JMESPathBindingEngine()
    context = {
        "step_1": {
            "total_inventory_value": 5000.0,
            "low_stock_skus": ["SKU-100"]
        }
    }
    target_tool_input_schema = {
        "title": "ConvertCurrencyInput",
        "properties": {
            "amount": {"type": "number"},
            "from_currency": {"type": "string"},
            "to_currency": {"type": "string"}
        }
    }

    from src.core.engine.engine import HeadlessExecutor
    
    executor = HeadlessExecutor(session=None, binding_engine=engine, enable_llm_fallback=True)
    from src.core.llm_client import get_llm_client
    executor.fallback_mapper = LLMFallbackMapper(model=get_llm_client())
    
    # Passing unresolved string inside an argument dictionary
    tool_args = {"amount": "$step_1.missing_field", "from_currency": "USD", "to_currency": "EUR"}
    
    res = executor._resolve_variables(
        tool_args,
        context,
        target_tool_input_schema=target_tool_input_schema,
        directive="Extract total_inventory_value and map to amount",
        enable_llm_fallback=True
    )
    assert res is not None
    assert res.get("amount") == 5000.0
    assert res.get("from_currency") == "USD"
if __name__ == "__main__":
    test_factory_creation()
    test_jmespath_binding_engine()
    test_jsonpath_binding_engine()
    test_dot_notation_binding_engine()
    test_llm_fallback_direct_mapping()
    test_jmespath_automatic_llm_fallback()
    print("All binding engine & LLM LangChain fallback tests passed successfully!")
