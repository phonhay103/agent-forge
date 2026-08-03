from typing import List, Optional
from pydantic import BaseModel, Field


class DynamicPlanTask(BaseModel):
    """Dynamic binding task. Planner decides tool + DAG order, runtime binds data."""
    id: str = Field(
        description=(
            "Unique, descriptive, snake_case task identifier "
            "(e.g., 'search_products', 'convert_currency'). Must be meaningful."
        )
    )
    tool_name: str = Field(description="Name of the MCP tool to execute")
    input_description: str = Field(
        description="Natural language description of what input data this task needs"
    )
    output_description: str = Field(
        description="Natural language description of what this task produces"
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task IDs whose outputs this task depends on"
    )
    reason: Optional[str] = Field(default=None, description="Why this tool was chosen")


class DynamicPlan(BaseModel):
    """Plan with tool selection but no variable expressions."""
    tasks: List[DynamicPlanTask] = Field(description="Ordered list of tasks with DAG dependencies")
    reason: Optional[str] = Field(default=None, description="Overall plan strategy")
