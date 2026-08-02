import re
from typing import List, Any, Optional, Dict, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo

class PlanStep(BaseModel):
    id: str = Field(description="Unique identifier for the step, e.g., step_1")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    args: Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]] = Field(
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$step_1.items')"
    )
    directive: Optional[str] = Field(
        default=None,
        description="Natural Language Data Mapping Directive explaining how outputs from previous steps should be mapped if fallback is enabled"
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reasoning or purpose behind this execution step"
    )

    @field_validator("args")
    @classmethod
    def validate_args_pattern(cls, v: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        regex_pattern = info.context.get("regex_pattern") if info.context else None
        if not regex_pattern:
            return v
        regex = re.compile(regex_pattern)

        def _check_value(val: Any):
            if isinstance(val, str) and val.startswith("$") and not val.startswith("__BINDING_FAILED"):
                if not regex.match(val):
                    raise ValueError(
                        f"Variable expression '{val}' does not conform to the active binding engine's representative regex pattern: {regex_pattern}"
                    )
            elif isinstance(val, dict):
                for item in val.values():
                    _check_value(item)
            elif isinstance(val, list):
                for item in val:
                    _check_value(item)

        _check_value(v)
        return v

class Plan(BaseModel):
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute sequentially")
    reason: Optional[str] = Field(
        default=None,
        description="Overall explanation of the plan strategy, routing path, and tool choices"
    )
