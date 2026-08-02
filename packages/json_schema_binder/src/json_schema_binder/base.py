from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


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
    def resolve(
        self,
        val: Any,
        context_store: Dict[str, Any],
        target_schema: Optional[Dict[str, Any]] = None,
        metadata_store: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Resolves variable references in a payload using context_store
        and optional schemas or metadata.
        """
        pass

    @abstractmethod
    def get_system_prompt_instruction(self) -> str:
        """Returns dynamic instructions for LLM System Prompt explaining how to format variable references."""
        pass
