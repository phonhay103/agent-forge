import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agent.planner import DynamicPlanner
from src.agent.models import DynamicPlan, DynamicPlanTask
from src.agent.executor import DynamicExecutor
from src.shared.executor_models import ExecutionContext

def test_dynamic_planner():
    planner = DynamicPlanner()
    available_tools = [
        {"name": "search", "description": "Search something"}
    ]
    mock_plan = DynamicPlan(
        tasks=[
            DynamicPlanTask(
                id="task_search",
                tool_name="search",
                input_description="Search for laptops",
                output_description="List of laptops",
                depends_on=[]
            )
        ],
        reason="Test plan"
    )
    with patch("src.agent.planner.run_structured_llm", return_value=mock_plan) as mock_run:
        plan = planner.create_plan("Search for laptops", available_tools)
        assert plan.tasks[0].id == "task_search"
        assert plan.tasks[0].tool_name == "search"
        mock_run.assert_called_once()

@pytest.mark.anyio
async def test_dynamic_executor():
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

    executor = DynamicExecutor(mcp_client)
    
    plan = DynamicPlan(
        tasks=[
            DynamicPlanTask(
                id="task_search",
                tool_name="search",
                input_description="Search for laptops",
                output_description="List of laptops",
                depends_on=[]
            )
        ],
        reason="Test plan"
    )
    
    mock_args = {"query": "laptops"}
    with patch.object(executor, "_llm_bind", return_value=mock_args) as mock_bind:
        ctx: ExecutionContext = await executor.run_plan(plan)
        assert len(ctx.results) == 1
        assert ctx.results[0].task_id == "task_search"
        assert ctx.results[0].output == {"results": ["laptop1", "laptop2"]}
        mcp_client.call_tool.assert_called_once_with(
            name="search",
            arguments={"query": "laptops"}
        )
        mock_bind.assert_called_once()


def test_dynamic_agent_prompt_injection():
    from prompt_composer import PromptComposer
    custom_prompt = PromptComposer().set_section("test_sec", "custom template text")
    
    planner = DynamicPlanner(prompt=custom_prompt)
    assert planner.prompt == custom_prompt
    
    executor = DynamicExecutor(
        AsyncMock(),
        prompt=custom_prompt
    )
    assert executor.prompt == custom_prompt

