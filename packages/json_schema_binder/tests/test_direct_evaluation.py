from pydantic import BaseModel

from json_schema_binder import (
    EvaluationResult,
    MappingResult,
    evaluate_expression,
    transform_schema,
)


class ShippingLabel(BaseModel):
    recipient: str
    item_count: int


def test_evaluate_expression_jmespath():
    source_data = {"order": {"customer": {"name": "Bob Smith"}, "items": [{"id": 1}, {"id": 2}, {"id": 3}]}}

    res_name = evaluate_expression("order.customer.name", source_data, engine="jmespath")
    assert isinstance(res_name, EvaluationResult)
    assert res_name.is_success is True
    assert res_name.value == "Bob Smith"

    res_count = evaluate_expression("length(order.items)", source_data, engine="jmespath")
    assert res_count.value == 3


def test_transform_schema():
    source_data = {"order": {"customer": {"name": "Bob Smith"}, "items": [{"id": 1}, {"id": 2}, {"id": 3}]}}

    mapping_spec = {"recipient": "order.customer.name", "item_count": "length(order.items)"}

    res = transform_schema(source_data, mapping_spec, engine="jmespath", target_schema=ShippingLabel)

    assert isinstance(res, MappingResult)
    assert res.is_success is True
    assert isinstance(res.output, ShippingLabel)
    assert res.output.recipient == "Bob Smith"
    assert res.output.item_count == 3
