from typing import List, Any, Optional, Dict, Union
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    id: str = Field(description="Unique identifier for the step, e.g., step_1")
    tool_name: str = Field(description="Name of the MCP tool to execute")
    args: Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]] = Field(
        description="Direct tool arguments matching the expected parameters, where each value is either a literal primitive (string/number/bool), a nested object/array, or a variable binding string starting with '$' (e.g., '$step_1.results...')"
    )
    directive: Optional[str] = Field(
        default=None,
        description="Natural Language Data Mapping Directive explaining how outputs from previous steps should be mapped if fallback is enabled"
    )
    reason: Optional[str] = Field(
        default=None,
        description="The reasoning or purpose behind this execution step"
    )

class Plan(BaseModel):
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute sequentially")
    reason: Optional[str] = Field(
        default=None,
        description="Overall explanation of the plan strategy, routing path, and tool choices"
    )
