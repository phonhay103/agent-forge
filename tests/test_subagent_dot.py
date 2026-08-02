from json_schema_binder import DotNotationBindingEngine
from pydantic import BaseModel
import sys


class DummyModel(BaseModel):
    id: int
    name: str


def test_dot_notation_valid_key():
    engine = DotNotationBindingEngine()
    context = {
        "step_1": {
            "result": {
                "user": "Alice"
            }
        }
    }
    resolved = engine.resolve("$step_1.result.user", context)
    assert resolved == "Alice", f"Expected 'Alice', got {resolved}"
    print("test_dot_notation_valid_key passed")


def test_dot_notation_with_lists():
    engine = DotNotationBindingEngine()
    context = {
        "step_1": {
            "items": ["a", "b", "c"]
        }
    }
    resolved = engine.resolve("$step_1.items.1", context)
    assert resolved == "b", f"Expected 'b', got {resolved}"
    print("test_dot_notation_with_lists passed")


def test_dot_notation_with_pydantic_model():
    engine = DotNotationBindingEngine()
    context = {
        "step_1": DummyModel(id=10, name="TestUser")
    }
    resolved = engine.resolve("$step_1.name", context)
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
