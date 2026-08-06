from collections.abc import Mapping
from typing import Any, Dict, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine
from json_schema_binder.engines import (
    DotNotationBindingEngine,
    JMESPathBindingEngine,
    JSONPathBindingEngine,
)
from json_schema_binder.factory import get_binding_engine
from json_schema_binder.models import (
    BindingContext,
    EvaluationResult,
    MappingResult,
    MappingSpec,
    SupportedDataType,
)
from json_schema_binder.parser import VariableParser
from json_schema_binder.template import TemplateResolver

T = TypeVar("T")


def evaluate_expression(
    expression: str,
    source_data: Any,
    engine: str | BaseBindingEngine = "jmespath",
) -> EvaluationResult[Any]:
    """
    Evaluates a single expression directly against source data.
    """
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    return binding_engine.evaluate(expression, source_data)


def transform_schema(
    source_data: Any,
    mapping_spec: dict[str, str] | MappingSpec,
    engine: str | BaseBindingEngine = "jmespath",
    target_schema: dict[str, Any] | type[BaseModel] | None = None,
) -> MappingResult[Any]:
    """
    Transforms source_data into a target payload using a direct mapping specification.
    """
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    return binding_engine.transform(source_data, mapping_spec, target_schema=target_schema)


def resolve_variables(
    payload: T,
    context: BindingContext | Mapping[str, Any],
    engine: str | BaseBindingEngine = "jmespath",
    target_schema: dict[str, Any] | type[BaseModel] | None = None,
) -> Any:
    """
    Convenience function to resolve variable expressions ($var...) in a template payload.
    Utilizes TemplateResolver for decoupled evaluation.
    """
    binding_ctx = BindingContext.from_dict(context)
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    resolver = TemplateResolver(engine=binding_engine)

    return resolver.resolve_payload(payload, binding_ctx)


__all__ = [
    "BaseBindingEngine",
    "BindingContext",
    "BindingType",
    "DotNotationBindingEngine",
    "EvaluationResult",
    "JMESPathBindingEngine",
    "JSONPathBindingEngine",
    "MappingResult",
    "MappingSpec",
    "SupportedDataType",
    "TemplateResolver",
    "VariableParser",
    "evaluate_expression",
    "get_binding_engine",
    "register_binding_engine",
    "resolve_variables",
    "transform_schema",
]


