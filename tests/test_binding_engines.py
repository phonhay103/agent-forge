from json_schema_binder import (
    get_binding_engine,
    BindingType,
    JMESPathBindingEngine,
    JSONPathBindingEngine,
    DotNotationBindingEngine,
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
        "products": [
            {"name": "Laptop", "price": 1200},
            {"name": "Mouse", "price": 25}
        ]
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: JMESPath" in instruction

    res = engine.evaluate("products[?price > `100`].name", context)
    assert res.value == ["Laptop"]


def test_jsonpath_binding_engine():
    engine = JSONPathBindingEngine()
    context = {
        "products": [
            {"name": "Laptop", "price": 1200},
            {"name": "Mouse", "price": 25}
        ]
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: JSONPath" in instruction

    res = engine.evaluate("$.products[?(@.price > 100)].name", context)
    assert res.value == ["Laptop"]

    res_single = engine.evaluate("$.products[0].name", context)
    assert res_single.value == "Laptop"


def test_dot_notation_binding_engine():
    engine = DotNotationBindingEngine()
    context = {
        "products": [
            {"name": "Laptop", "price": 1200},
            {"name": "Mouse", "price": 25}
        ]
    }

    instruction = engine.get_system_prompt_instruction()
    assert "Variable Binding Engine: Dot Notation" in instruction

    res = engine.evaluate("products.0.name", context)
    assert res.value == "Laptop"


if __name__ == "__main__":
    test_factory_creation()
    test_jmespath_binding_engine()
    test_jsonpath_binding_engine()
    test_dot_notation_binding_engine()
    print("All binding engine tests passed successfully!")
