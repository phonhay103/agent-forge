import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.abstract_agent.planner import AbstractPlanner
from src.abstract_agent.models import AbstractPlan, AbstractPlanTask
from src.abstract_agent.executor import AbstractExecutor, ToolSelection
from src.shared.executor_models import ExecutionContext

def test_abstract_planner():
    planner = AbstractPlanner()
    available_tools = [
        {"name": "search", "description": "Search something"}
    ]
    mock_plan = AbstractPlan(
        tasks=[
            AbstractPlanTask(
                id="task_search",
                intent="Search for laptops",
                expected_input="NL query",
                expected_output="List of laptops",
                depends_on=[]
            )
        ],
        reason="Test plan"
    )
    with patch("src.abstract_agent.planner.run_structured_llm", return_value=mock_plan) as mock_run:
        plan = planner.create_plan("Search for laptops", available_tools)
        assert plan.tasks[0].id == "task_search"
        assert plan.tasks[0].intent == "Search for laptops"
        mock_run.assert_called_once()

@pytest.mark.anyio
async def test_abstract_executor():
    mcp_client = AsyncMock()
    mock_tool = MagicMock()
    mock_tool.name = "search"
    mock_tool.input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        }
    }
    mock_tools_response = MagicMock()
    mock_tools_response.tools = [mock_tool]
    mcp_client.list_tools = AsyncMock(return_value=mock_tools_response)
    
    mock_result_content = MagicMock()
    mock_result_content.text = '{"results": ["laptop1", "laptop2"]}'
    mock_call_result = MagicMock()
    mock_call_result.content = [mock_result_content]
    mcp_client.call_tool = AsyncMock(return_value=mock_call_result)

    executor = AbstractExecutor(mcp_client)
    
    plan = AbstractPlan(
        tasks=[
            AbstractPlanTask(
                id="task_search",
                intent="Search for laptops",
                expected_input="NL query",
                expected_output="List of laptops",
                depends_on=[]
            )
        ],
        reason="Test plan"
    )
    
    mock_tool_selection = ToolSelection(
        tool_name="search",
        confidence=0.9,
        reasoning="Matches search intent"
    )
    mock_args = {"query": "laptops"}
    
    with patch.object(executor, "_resolve_tool", return_value=mock_tool_selection) as mock_resolve:
        with patch.object(executor, "_llm_bind", return_value=mock_args) as mock_bind:
            ctx: ExecutionContext = await executor.run_plan(plan)
            assert len(ctx.results) == 1
            assert ctx.results[0].task_id == "task_search"
            assert ctx.results[0].tool_name == "search"
            assert ctx.results[0].output == {"results": ["laptop1", "laptop2"]}
            mcp_client.call_tool.assert_called_once_with(
                name="search",
                arguments={"query": "laptops"}
            )
            mock_resolve.assert_called_once()
            mock_bind.assert_called_once()
