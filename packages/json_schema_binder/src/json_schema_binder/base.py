from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, TypeVar, Union, Type
from pydantic import BaseModel

from json_schema_binder.models import (
    BindingContext,
    EvaluationResult,
    MappingResult,
    MappingSpec,
    SupportedDataType,
)

T = TypeVar("T")


class BindingType(str, Enum):
    JMESPATH = "jmespath"
    JSONPATH = "jsonpath"
    DOT_NOTATION = "dot_notation"


_BINDING_ENGINES_REGISTRY: Dict[str, Any] = {}


def register_binding_engine(name: str):
    """Decorator to register a concrete binding engine class."""
    def decorator(cls):
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
        mapping_spec: Union[Dict[str, str], MappingSpec],
        target_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
    ) -> MappingResult[Any]:
        """
        Transforms source_data into a target dictionary or BaseModel using a direct mapping specification.
        """
        pass

    @abstractmethod
    def get_system_prompt_instruction(self) -> str:
        """Returns dynamic instructions for LLM System Prompt explaining how to format variable references."""
        pass


