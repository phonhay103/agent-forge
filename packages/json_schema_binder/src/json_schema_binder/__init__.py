from typing import Any, Dict, Optional, Union, TypeVar, Type, Mapping
from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine
from json_schema_binder.engines import (
    JMESPathBindingEngine,
    JSONPathBindingEngine,
    DotNotationBindingEngine,
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
    engine: Union[str, BaseBindingEngine] = "jmespath",
) -> EvaluationResult[Any]:
    """
    Evaluates a single expression directly against source data.
    """
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    return binding_engine.evaluate(expression, source_data)


def transform_schema(
    source_data: Any,
    mapping_spec: Union[Dict[str, str], MappingSpec],
    engine: Union[str, BaseBindingEngine] = "jmespath",
    target_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
) -> MappingResult[Any]:
    """
    Transforms source_data into a target payload using a direct mapping specification.
    """
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    return binding_engine.transform(source_data, mapping_spec, target_schema=target_schema)


def resolve_variables(
    payload: T,
    context: Union[BindingContext, Mapping[str, Any]],
    engine: Union[str, BaseBindingEngine] = "jmespath",
    target_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
    fallback_mapper: Optional[Any] = None,
    directive: Optional[str] = None,
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
    "BindingType",
    "register_binding_engine",
    "JMESPathBindingEngine",
    "JSONPathBindingEngine",
    "DotNotationBindingEngine",
    "get_binding_engine",
    "VariableParser",
    "TemplateResolver",
    "evaluate_expression",
    "transform_schema",
    "resolve_variables",
    "BindingContext",
    "EvaluationResult",
    "MappingResult",
    "MappingSpec",
    "SupportedDataType",
]


