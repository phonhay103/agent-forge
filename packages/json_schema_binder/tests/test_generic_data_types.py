from dataclasses import dataclass

from pydantic import BaseModel

from json_schema_binder import (
    BaseBindingEngine,
    BindingContext,
    BindingType,
    EvaluationResult,
    MappingResult,
    evaluate_expression,
    get_binding_engine,
    register_binding_engine,
    resolve_variables,
)


class UserProfile(BaseModel):
    name: str
    email: str
    age: int


@dataclass
class OrderItem:
    product_id: str
    price: float
    qty: int


def test_pydantic_context_and_payload():
    user = UserProfile(name="Alice", email="alice@example.com", age=30)
    context = {"user_data": user}

    # Test Pydantic model payload resolution via template resolver
    payload = {"account_name": "$user_data.name", "contact": "$user_data.email"}
    res = resolve_variables(payload, context, engine="dot_notation")

    assert res == {"account_name": "Alice", "contact": "alice@example.com"}


def test_dataclass_context():
    item = OrderItem(product_id="P100", price=49.99, qty=2)
    context = BindingContext.from_dict({"order": item})

    res = evaluate_expression("order.price", context, engine="jmespath")
    assert res.is_success is True
    assert res.value == 49.99


def test_root_context_direct_evaluation():
    context = {
        "products": [
            {"id": "P1", "title": "Keyboard", "price": 100},
            {"id": "P2", "title": "Monitor", "price": 300},
        ]
    }

    # JMESPath evaluated directly against context root
    res = evaluate_expression("products[?price > `150`].title", context, engine="jmespath")
    assert res.is_success is True
    assert res.value == ["Monitor"]


def test_custom_binding_engine_registration():
    @register_binding_engine("upper_custom")
    class UpperCustomEngine(BaseBindingEngine):
        @property
        def binding_type(self) -> BindingType:
            return BindingType.DOT_NOTATION

        def evaluate(self, expression, source_data):
            if isinstance(source_data, dict) and expression in source_data:
                val = source_data[expression]
                if isinstance(val, str):
                    val = val.upper()
                return EvaluationResult(
                    value=val,
                    expression=expression,
                    is_success=True,
                    engine="upper_custom",
                )
            return EvaluationResult(
                value=None,
                expression=expression,
                is_success=False,
                engine="upper_custom",
            )

        def transform(self, source_data, mapping_spec, target_schema=None):
            return MappingResult(
                output={},
                is_success=True,
                engine="upper_custom",
            )

        def get_system_prompt_instruction(self):
            return "Upper custom engine"

    custom_engine = get_binding_engine("upper_custom")
    assert custom_engine is not None

    res = custom_engine.evaluate("msg", {"msg": "hello world"})
    assert res.value == "HELLO WORLD"
