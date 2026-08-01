import pytest
from unittest.mock import MagicMock
from src.core.engine.engine import HeadlessExecutor
from src.core.planner.models import Plan, PlanStep

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
        enable_llm_fallback=False
    )
    
    # Create a plan with an unresolved step reference
    plan = Plan(
        steps=[
            PlanStep(
                id="step_1",
                tool_name="some_tool",
                args={"param": "$step_non_existent.results"}
            )
        ]
    )
    
    # Running the plan should raise a ValueError and stop execution immediately
    with pytest.raises(ValueError, match="Execution Halted: Variable binding failed for step 'step_1'"):
        await executor.run_plan(plan)
