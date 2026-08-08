from typing import Any

from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    """Result from executing a single task."""

    task_id: str
    tool_name: str
    output: Any


class ExecutionContext(BaseModel):
    """Accumulates results across all tasks in a plan execution."""

    results: list[TaskResult] = Field(default_factory=list)
    store: dict[str, Any] = Field(default_factory=dict)

    def add_result(self, task_id: str, tool_name: str, output: Any) -> None:
        self.results.append(TaskResult(task_id=task_id, tool_name=tool_name, output=output))
        self.store[task_id] = output
