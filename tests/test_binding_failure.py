import pytest
from unittest.mock import MagicMock
from src.agent.executor import StaticExecutor as HeadlessExecutor
from src.agent.models import Plan, PlanTask as PlanStep

@pytest.mark.anyio
async def test_binding_failure_stops_execution():
    from unittest.mock import AsyncMock
    mcp_client = AsyncMock()
    mock_tools_response = MagicMock()
    mock_tools_response.tools = []
    mcp_client.list_tools = AsyncMock(return_value=mock_tools_response)
    # Initialize HeadlessExecutor
    executor = HeadlessExecutor(
        mcp_client,
        binding_engine="jmespath",
    )
    
    # Create a plan with an unresolved task reference
    plan = Plan(
        tasks=[
            PlanStep(
                id="task_1",
                tool_name="some_tool",
                args={"param": "$task_non_existent.results"}
            )
        ]
    )
    
    # Running the plan should raise a ValueError and stop execution immediately
    with pytest.raises(ValueError, match="Execution Halted: Variable binding failed for task 'task_1'"):
        await executor.run_plan(plan)
