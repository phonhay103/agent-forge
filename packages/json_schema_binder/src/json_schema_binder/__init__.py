from typing import Any, Dict, Optional, Union

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine
from json_schema_binder.engines import (
    JMESPathBindingEngine,
    JSONPathBindingEngine,
    DotNotationBindingEngine,
)
from json_schema_binder.factory import get_binding_engine
from json_schema_binder.fallback import LLMFallbackMapper
from json_schema_binder.parser import VariableParser
from json_schema_binder.protocols import FallbackResolverProtocol


def resolve_variables(
    payload: Any,
    context_store: Dict[str, Any],
    engine: Union[str, BaseBindingEngine] = "jmespath",
    target_schema: Optional[Dict[str, Any]] = None,
    fallback_mapper: Optional[FallbackResolverProtocol] = None,
    directive: Optional[str] = None,
) -> Any:
    """
    Convenience function to resolve variable references ($step_...) within any payload.
    Supports deterministic binding (JMESPath/JSONPath/Dot) and optional LLM Fallback mapping.
    """
    binding_engine = get_binding_engine(engine) if isinstance(engine, str) else engine
    resolved = binding_engine.resolve(
        payload,
        context_store,
        target_schema=target_schema,
    )

    if fallback_mapper and target_schema and VariableParser.has_unresolved_references(resolved):
        resolved = fallback_mapper.repair_payload(
            context_store=context_store,
            target_schema=target_schema,
            partially_resolved_payload=resolved,
            directive=directive,
        )

    return resolved


__all__ = [
    "BaseBindingEngine",
    "BindingType",
    "register_binding_engine",
    "JMESPathBindingEngine",
    "JSONPathBindingEngine",
    "DotNotationBindingEngine",
    "LLMFallbackMapper",
    "get_binding_engine",
    "VariableParser",
    "FallbackResolverProtocol",
    "resolve_variables",
]
