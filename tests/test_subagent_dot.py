import sys

from pydantic import BaseModel

from json_schema_binder import DotNotationBindingEngine


class DummyModel(BaseModel):
    id: int
    name: str


def test_dot_notation_valid_key():
    engine = DotNotationBindingEngine()
    context = {"step_1": {"result": {"user": "Alice"}}}
    resolved = engine.evaluate("step_1.result.user", context).value
    assert resolved == "Alice", f"Expected 'Alice', got {resolved}"
    print("test_dot_notation_valid_key passed")


def test_dot_notation_with_lists():
    engine = DotNotationBindingEngine()
    context = {"step_1": {"items": ["a", "b", "c"]}}
    resolved = engine.evaluate("step_1.items.1", context).value
    assert resolved == "b", f"Expected 'b', got {resolved}"
    print("test_dot_notation_with_lists passed")


def test_dot_notation_with_pydantic_model():
    engine = DotNotationBindingEngine()
    context = {"step_1": DummyModel(id=10, name="TestUser")}
    resolved = engine.evaluate("step_1.name", context).value
    assert resolved == "TestUser", f"Expected 'TestUser', got {resolved}"
    print("test_dot_notation_with_pydantic_model passed")


if __name__ == "__main__":
    try:
        test_dot_notation_valid_key()
        test_dot_notation_with_lists()
        test_dot_notation_with_pydantic_model()
        print("All Dot Notation tests passed successfully!")
        sys.exit(0)
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
