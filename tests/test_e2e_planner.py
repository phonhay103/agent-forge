import asyncio
from dotenv import load_dotenv
load_dotenv()
from httpx import AsyncClient
from src.core.planner.planner import Planner
from src.core.engine.engine import HeadlessExecutor
from src.core.test_inputs import TEST_SUITE
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
    
    print(f"[{test_id}] Plan generated with {len(plan.steps)} steps")
    for step in plan.steps:
        print(f"[{test_id}] Step: {step.tool_name}, Directive: {getattr(step, 'directive', None)}")
        
    return plan

if __name__ == "__main__":
    async def main():
        # Test 1: JMESPath with Fallback
        await run_e2e_test("T1", "Search for global tech supply chain and analyze its supply chain structure.", "jmespath", True)
        
        # Test 2: JSONPath without Fallback
        await run_e2e_test("T2", "Search for Acme Corp org structure and process the organization data.", "jsonpath", False)
        
    asyncio.run(main())