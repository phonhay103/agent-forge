from pydantic import BaseModel, Field


class AbstractPlanTask(BaseModel):
    """Abstract task — Planner only describes intent. Runtime resolves tool selection and data binding."""

    id: str = Field(
        description=(
            "Unique, descriptive, snake_case task identifier "
            "(e.g., 'find_products', 'transform_prices'). Must be meaningful."
        )
    )
    intent: str = Field(description="Natural language description of what this task should accomplish")
    expected_input: str | None = Field(default=None, description="Natural language description of input needed")
    expected_output: str | None = Field(default=None, description="Natural language description of output produced")
    depends_on: list[str] = Field(
        default_factory=list, description="List of task IDs whose outputs this task depends on"
    )
    reason: str | None = Field(default=None)


class AbstractPlan(BaseModel):
    """Plan with only task intents — no tool names, no variable expressions."""

    tasks: list[AbstractPlanTask] = Field(description="Ordered list of abstract tasks")
    reason: str | None = Field(default=None, description="Overall plan strategy")
