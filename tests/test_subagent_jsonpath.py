import sys

from pydantic import BaseModel

from json_schema_binder import JSONPathBindingEngine


class DummyModel(BaseModel):
    value: int


def test_jsonpath_valid_key():
    engine = JSONPathBindingEngine()
    context = {
        "step_1": {
            "key1": "value1",
            "nested": {
                "key2": "value2"
            }
        }
    }
    resolved = engine.evaluate("step_1.key1", context).value
    assert resolved == "value1", f"Expected 'value1', got {resolved}"
    print("test_jsonpath_valid_key passed")


def test_jsonpath_with_nested_objects():
    engine = JSONPathBindingEngine()
    context = {
        "step_1": {
            "nested": {
                "key2": "value2"
            }
        }
    }
    resolved = engine.evaluate("step_1.nested.key2", context).value
    assert resolved == "value2", f"Expected 'value2', got {resolved}"
    print("test_jsonpath_with_nested_objects passed")


def test_jsonpath_with_pydantic_model():
    engine = JSONPathBindingEngine()
    context = {
        "step_2": DummyModel(value=42)
    }
    resolved = engine.evaluate("step_2.value", context).value
    assert resolved == 42, f"Expected 42, got {resolved}"
    print("test_jsonpath_with_pydantic_model passed")




if __name__ == "__main__":
    try:
        test_jsonpath_valid_key()
        test_jsonpath_with_nested_objects()
        test_jsonpath_with_pydantic_model()
        print("All JSONPath tests passed successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
