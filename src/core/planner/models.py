from typing import List, Any, Optional
from pydantic import BaseModel, Field

class StepArgument(BaseModel):
    input: Any = Field(description="The input object or data model required for the tool execution")

class PlanStep(BaseModel):
    id: str = Field(description="Unique identifier for the step, e.g., step_1")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    args: StepArgument = Field(description="Arguments for the tool execution")
    directive: Optional[str] = Field(
        default=None,
        description="Natural Language Data Mapping Directive explaining how outputs from previous steps should be mapped if fallback is enabled"
    )

class Plan(BaseModel):
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute sequentially")
