import re
from typing import Any, List

# Match variable reference prefix (e.g., "$var_1", "$step_1", "$var_name")
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
        if isinstance(v, (str, int, float, bool, bytes)) or v is None:
            return False
        if isinstance(v, dict):
            return any(cls.has_unresolved_references(val) for val in v.values())
        if isinstance(v, list):
            return any(cls.has_unresolved_references(val) for val in v)
        if hasattr(v, "model_dump"):
            return cls.has_unresolved_references(v.model_dump())
        return False

    @classmethod
    def extract_unresolved_references(cls, v: Any) -> List[str]:
        """
        Recursively collects all unresolved variable reference strings in a payload.
        """
        unresolved: List[str] = []
        if cls.is_variable_reference(v):
            unresolved.append(str(v))
        elif isinstance(v, dict):
            for val in v.values():
                unresolved.extend(cls.extract_unresolved_references(val))
        elif isinstance(v, list):
            for val in v:
                unresolved.extend(cls.extract_unresolved_references(val))
        elif hasattr(v, "model_dump"):
            unresolved.extend(cls.extract_unresolved_references(v.model_dump()))
        return unresolved

