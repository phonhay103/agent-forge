import asyncio
from dotenv import load_dotenv
load_dotenv()
from httpx import AsyncClient
from src.static_agent.planner import Planner
from src.static_agent.executor import StaticExecutor as HeadlessExecutor
from src.shared.test_inputs import TEST_SUITE
async def run_e2e_test(test_id, test_query, binding_type, enable_llm_fallback):
    print(f"[{test_id}] Starting E2E test with fallback={enable_llm_fallback}")
    
    # Fake tools metadata
    tools_metadata = [
        {
            "name": "search",
            "description": "Searches for general information or market data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "analyze_supply_chain",
            "description": "Analyzes a 5-level nested supply chain structure.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "network_info": {"type": "object"},
                    "regions": {"type": "array"}
                },
                "required": ["network_info", "regions"]
            }
        },
        {
             "name": "calculate",
             "description": "Evaluates a mathematical expression.",
             "inputSchema": {
                 "type": "object",
                 "properties": {
                     "expression": {"type": "string"}
                 },
                 "required": ["expression"]
             }
        }
    ]

    planner = Planner()
    plan = planner.create_plan(
        test_query,
        tools_metadata,
        binding_type=binding_type,
        enable_llm_fallback=enable_llm_fallback
    )
    
    print(f"[{test_id}] Plan generated with {len(plan.tasks)} tasks")
    for task in plan.tasks:
        print(f"[{test_id}] Task: {task.tool_name}, Directive: {getattr(task, 'directive', None)}")
        
    return plan

import pytest
import os

@pytest.mark.anyio
async def test_e2e_planner_jmespath():
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY is not set.")
    await run_e2e_test("T1", "Search for global tech supply chain and analyze its supply chain structure.", "jmespath", True)

@pytest.mark.anyio
async def test_e2e_planner_jsonpath():
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY is not set.")
    await run_e2e_test("T2", "Search for Acme Corp org structure and process the organization data.", "jsonpath", False)


def test_static_agent_injection():
    from prompt_composer import PromptComposer
    from json_schema_binder.fallback import LLMFallbackMapper
    from unittest.mock import AsyncMock, MagicMock
    
    custom_prompt = PromptComposer().set_section("test_sec", "custom template text")
    planner = Planner(prompt=custom_prompt)
    assert planner.prompt == custom_prompt
    
    mock_fallback_mapper = LLMFallbackMapper(model=MagicMock())
    executor = HeadlessExecutor(
        session=AsyncMock(),
        enable_llm_fallback=True,
        fallback_mapper=mock_fallback_mapper
    )
    assert executor.fallback_mapper == mock_fallback_mapper