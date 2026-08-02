from pydantic import BaseModel
from json_schema_binder import (
    resolve_variables,
    get_binding_engine,
    BindingType,
    JMESPathBindingEngine,
    JSONPathBindingEngine,
    DotNotationBindingEngine,
    VariableParser,
)


def test_factory():
    jmes = get_binding_engine("jmespath")
    assert isinstance(jmes, JMESPathBindingEngine)
    assert jmes.binding_type == BindingType.JMESPATH

    jsonpath = get_binding_engine("jsonpath")
    assert isinstance(jsonpath, JSONPathBindingEngine)
    assert jsonpath.binding_type == BindingType.JSONPATH

    dot = get_binding_engine("dot_notation")
    assert isinstance(dot, DotNotationBindingEngine)
    assert dot.binding_type == BindingType.DOT_NOTATION


def test_jmespath_resolution():
    context = {
        "step_1": {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 20}
            ]
        }
    }
    res = resolve_variables({"adults": "$step_1.users[?age >= `25`].name"}, context, engine="jmespath")
    assert res == {"adults": ["Alice"]}


def test_jsonpath_resolution():
    context = {
        "step_1": {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 20}
            ]
        }
    }
    res = resolve_variables({"adults": "$step_1.users[?(@.age >= 25)].name"}, context, engine="jsonpath")
    assert res == {"adults": ["Alice"]}


def test_dot_notation_resolution():
    context = {
        "step_1": {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 20}
            ]
        }
    }
    res = resolve_variables({"first_user": "$step_1.users.0.name"}, context, engine="dot_notation")
    assert res == {"first_user": "Alice"}




def test_variable_parser():
    assert VariableParser.is_variable_reference("$step_1.foo")
    assert VariableParser.is_variable_reference("$step_calc.bar")
    assert not VariableParser.is_variable_reference("step_1.foo")

    assert VariableParser.has_unresolved_references({"a": "$step_1.missing"})
    assert not VariableParser.has_unresolved_references({"a": "resolved_value"})
