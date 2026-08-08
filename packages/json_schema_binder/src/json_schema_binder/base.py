from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel

from json_schema_binder.models import (
    EvaluationResult,
    MappingResult,
    MappingSpec,
)

T = TypeVar("T")


class BindingType(StrEnum):
    JMESPATH = "jmespath"
    JSONPATH = "jsonpath"
    DOT_NOTATION = "dot_notation"


_BINDING_ENGINES_REGISTRY: dict[str, Any] = {}


def register_binding_engine(name: str) -> Callable[[Any], Any]:
    """Decorator to register a concrete binding engine class."""

    def decorator(cls: Any) -> Any:
        _BINDING_ENGINES_REGISTRY[name.lower().strip()] = cls
        return cls

    return decorator


class BaseBindingEngine(ABC):
    @property
    @abstractmethod
    def binding_type(self) -> BindingType:
        """Returns the binding engine type identifier."""
        pass

    @abstractmethod
    def evaluate(self, expression: str, source_data: Any) -> EvaluationResult[Any]:
        """
        Evaluates a single expression string directly against source_data.
        """
        pass

    @abstractmethod
    def transform(
        self,
        source_data: Any,
        mapping_spec: dict[str, str] | MappingSpec,
        target_schema: dict[str, Any] | type[BaseModel] | None = None,
    ) -> MappingResult[Any]:
        """
        Transforms source_data into a target dictionary or BaseModel using a direct mapping specification.
        """
        pass

    @abstractmethod
    def get_system_prompt_instruction(self) -> str:
        """Returns dynamic instructions for LLM System Prompt explaining how to format variable references."""
        pass

    def get_regex_pattern(self) -> str | None:
        """Returns the official representative regex pattern for this binding engine, or None if not defined."""
        return None
