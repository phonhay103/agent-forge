import re
from typing import Any

# Match variable reference prefix (e.g., "$var_1", "$step_1", "$step_calculate")
VAR_REF_RE = re.compile(r"^\$[a-zA-Z0-9_]+")


class VariableParser:
    """
    Utility for detecting and validating variable references
    and unresolved variables within payloads.
    """
    @staticmethod
    def is_variable_reference(val: Any) -> bool:
        """Checks if a value is a string starting with an unresolved variable reference (e.g. $var_name)."""
        return isinstance(val, str) and bool(VAR_REF_RE.match(val))

    @classmethod
    def has_unresolved_references(cls, v: Any) -> bool:
        """
        Recursively checks if a payload (dict, list, string, or BaseModel) 
        contains any unresolved variable references.
        """
        if cls.is_variable_reference(v):
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
