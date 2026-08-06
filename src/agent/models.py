import re
from typing import List, Any, Optional, Dict, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from enum import Enum

class BindingType(str, Enum):
    DOT = "dot"
    JSONPATH = "jsonpath"
    JMESPATH = "jmespath"

class DynamicBindingMode(str, Enum):
    JMESPATH_VALIDATE = "jmespath_validate"
    LLM_DIRECT = "llm_direct"

def _validate_args_pattern_helper(v: Optional[Dict[str, Any]], info: ValidationInfo) -> Optional[Dict[str, Any]]:
    if v is None:
        return v
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

class StaticPlanTask(BaseModel):
    id: str = Field(description="Unique identifier for the task, e.g., 'search_products'")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    args: Optional[Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]]] = Field(
        default=None,
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$task_search_products.items')"
    )
    directive: Optional[str] = Field(
        default=None,
        description="Natural Language Data Mapping Directive explaining how outputs from previous steps should be mapped if fallback is enabled"
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs whose outputs this task depends on"
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reasoning or purpose behind this execution step"
    )

    @field_validator("args")
    @classmethod
    def validate_args_pattern(cls, v: Optional[Dict[str, Any]], info: ValidationInfo) -> Optional[Dict[str, Any]]:
        return _validate_args_pattern_helper(v, info)

class StaticPlan(BaseModel):
    tasks: List[StaticPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: Optional[str] = Field(
        default=None,
        description="Overall explanation of the plan strategy, routing path, and tool choices"
    )

class DynamicPlanTask(BaseModel):
    id: str = Field(description="Unique identifier for the task, e.g., 'search_products'")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    input_description: Optional[str] = Field(
        default=None,
        description="Natural language description of input data needed"
    )
    output_description: Optional[str] = Field(
        default=None,
        description="Natural language description of output produced"
    )
    args_jmespath: Optional[str] = Field(
        default=None,
        description="Pre-planned JMESPath mapping path, or null if schema is missing or not applicable"
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs whose outputs this task depends on"
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reasoning or purpose behind this execution step"
    )

class DynamicPlan(BaseModel):
    tasks: List[DynamicPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: Optional[str] = Field(
        default=None,
        description="Overall explanation of the plan strategy, routing path, and tool choices"
    )

class UnifiedPlanTask(BaseModel):
    id: str = Field(description="Unique identifier for the task, e.g., 'search_products'")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    
    # Static mode fields
    args: Optional[Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]]] = Field(
        default=None,
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$task_search_products.items')"
    )
    directive: Optional[str] = Field(
        default=None,
        description="Natural Language Data Mapping Directive explaining how outputs from previous steps should be mapped if fallback is enabled"
    )
    
    # Dynamic/hybrid mode fields
    input_description: Optional[str] = Field(
        default=None,
        description="Natural language description of input data needed"
    )
    output_description: Optional[str] = Field(
        default=None,
        description="Natural language description of output produced"
    )
    args_jmespath: Optional[str] = Field(
        default=None,
        description="Pre-planned JMESPath mapping path, or null if schema is missing or not applicable"
    )

    # General fields
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs whose outputs this task depends on"
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reasoning or purpose behind this execution step"
    )

    @field_validator("args")
    @classmethod
    def validate_args_pattern(cls, v: Optional[Dict[str, Any]], info: ValidationInfo) -> Optional[Dict[str, Any]]:
        return _validate_args_pattern_helper(v, info)

class UnifiedPlan(BaseModel):
    tasks: List[UnifiedPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: Optional[str] = Field(
        default=None,
        description="Overall explanation of the plan strategy, routing path, and tool choices"
    )

# Backward compatibility aliases
PlanTask = StaticPlanTask
PlanStep = StaticPlanTask
Plan = StaticPlan
