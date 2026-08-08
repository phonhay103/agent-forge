import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class BindingType(StrEnum):
    DOT = "dot"
    JSONPATH = "jsonpath"
    JMESPATH = "jmespath"


class DynamicBindingMode(StrEnum):
    JMESPATH_VALIDATE = "jmespath_validate"
    LLM_DIRECT = "llm_direct"


def _validate_args_pattern_helper(v: dict[str, Any] | None, info: ValidationInfo) -> dict[str, Any] | None:
    if v is None:
        return v
    regex_pattern = info.context.get("regex_pattern") if info.context else None
    if not regex_pattern:
        return v
    regex = re.compile(regex_pattern)

    def _check_value(val: Any) -> None:
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
    args: dict[str, str | int | float | bool | list[Any] | dict[str, Any]] | None = Field(
        default=None,
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$task_search_products.items')",
    )
    depends_on: list[str] = Field(
        default_factory=list, description="List of task IDs whose outputs this task depends on"
    )
    reason: str | None = Field(default=None, description="The reasoning or purpose behind this execution step")

    @field_validator("args")
    @classmethod
    def validate_args_pattern(cls, v: dict[str, Any] | None, info: ValidationInfo) -> dict[str, Any] | None:
        return _validate_args_pattern_helper(v, info)


class StaticPlan(BaseModel):
    tasks: list[StaticPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: str | None = Field(
        default=None, description="Overall explanation of the plan strategy, routing path, and tool choices"
    )


class DynamicPlanTask(BaseModel):
    id: str = Field(description="Unique identifier for the task, e.g., 'search_products'")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    input_description: str | None = Field(default=None, description="Natural language description of input data needed")
    output_description: str | None = Field(default=None, description="Natural language description of output produced")
    args_jmespath: str | None = Field(
        default=None, description="Pre-planned JMESPath mapping path, or null if schema is missing or not applicable"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="List of task IDs whose outputs this task depends on"
    )
    reason: str | None = Field(default=None, description="The reasoning or purpose behind this execution step")


class DynamicPlan(BaseModel):
    tasks: list[DynamicPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: str | None = Field(
        default=None, description="Overall explanation of the plan strategy, routing path, and tool choices"
    )


class UnifiedPlanTask(BaseModel):
    id: str = Field(description="Unique identifier for the task, e.g., 'search_products'")
    tool_name: str = Field(description="Name of the MCP tool to execute")

    # Static mode fields
    args: dict[str, str | int | float | bool | list[Any] | dict[str, Any]] | None = Field(
        default=None,
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$task_search_products.items')",
    )
    # Dynamic/hybrid mode fields
    input_description: str | None = Field(default=None, description="Natural language description of input data needed")
    output_description: str | None = Field(default=None, description="Natural language description of output produced")
    args_jmespath: str | None = Field(
        default=None, description="Pre-planned JMESPath mapping path, or null if schema is missing or not applicable"
    )

    # General fields
    depends_on: list[str] = Field(
        default_factory=list, description="List of task IDs whose outputs this task depends on"
    )
    reason: str | None = Field(default=None, description="The reasoning or purpose behind this execution step")

    @field_validator("args")
    @classmethod
    def validate_args_pattern(cls, v: dict[str, Any] | None, info: ValidationInfo) -> dict[str, Any] | None:
        return _validate_args_pattern_helper(v, info)


class UnifiedPlan(BaseModel):
    tasks: list[UnifiedPlanTask] = Field(description="Ordered list of tasks to execute sequentially")
    reason: str | None = Field(
        default=None, description="Overall explanation of the plan strategy, routing path, and tool choices"
    )


# Backward compatibility aliases
PlanTask = StaticPlanTask
PlanStep = StaticPlanTask
Plan = StaticPlan
