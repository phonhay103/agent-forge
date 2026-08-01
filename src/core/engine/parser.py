import re
from typing import Any

# Match step reference prefix (e.g., "$step_1", "$step_calculate")
STEP_REF_RE = re.compile(r"^\$step_[a-zA-Z0-9_]+")

class VariableParser:
    """
    Highly cohesive utility for detecting and validating variable references
    and unresolved step variables within tool argument payloads.
    """
    @staticmethod
    def is_step_reference(val: Any) -> bool:
        """Checks if a value is a string starting with an unresolved step reference ($step_)."""
        return isinstance(val, str) and bool(STEP_REF_RE.match(val))

    @classmethod
    def has_unresolved_references(cls, v: Any) -> bool:
        """
        Recursively checks if a payload (dict, list, string, or BaseModel) 
        contains any unresolved step references.
        """
        if cls.is_step_reference(v):
            return True
        if isinstance(v, (str, int, float, bool)) or v is None:
            return False
        if isinstance(v, dict):
            return any(cls.has_unresolved_references(val) for val in v.values())
        if isinstance(v, list):
            return any(cls.has_unresolved_references(val) for val in v)
        if hasattr(v, "model_dump"):
            return cls.has_unresolved_references(v.model_dump())
        return False
