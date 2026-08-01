import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from src.core.planner.planner import Planner, Plan
from src.core.engine.engine import HeadlessExecutor, ExecutionContext
from src.core.engine.protocols import MCPClient
from src.core.test_inputs import TEST_SUITE, TestCase
from src.core.main import ensure_server_running, MCP_SERVER_URL

load_dotenv()

async def run_single_test(tc: TestCase, binding_type: str = "jmespath", enable_llm_fallback: bool = False):
    server_proc = await ensure_server_running(MCP_SERVER_URL)
    report = {
        "id": tc.id,
        "name": tc.name,
        "category": tc.category,
        "query": tc.query,
        "status": "UNKNOWN",
        "plan": None,
        "execution": None,
        "error": None
    }
    
    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_list = await session.list_tools()
                tools_metadata = [t.model_dump() for t in tools_list.tools]
                
                planner = Planner()
                plan: Plan = planner.create_plan(
                    tc.query,
                    tools_metadata,
                    binding_type=binding_type,
                    enable_llm_fallback=enable_llm_fallback
                )
                report["plan"] = plan.model_dump()
                
                mcp_client = MCPClient(session)
                executor = HeadlessExecutor(
                    mcp_client,
                    binding_engine=binding_type,
                    enable_llm_fallback=enable_llm_fallback
                )
                
                try:
                    results: ExecutionContext = await executor.run_plan(plan)
                    report["execution"] = results.model_dump()
                    report["status"] = "PASSED"
                except ValueError as ve:
                    report["status"] = "HALTED_BY_DESIGN" if "__BINDING_FAILED_TOKEN" in str(ve) else "FAILED"
                    report["error"] = str(ve)
                except Exception as e:
                    report["status"] = "FAILED"
                    report["error"] = str(e)
    except Exception as outer_e:
        report["status"] = "SERVER_ERROR"
        report["error"] = str(outer_e)
    finally:
        if server_proc:
            try:
                server_proc.terminate()
                server_proc.wait(timeout=2)
            except Exception:
                pass
                
    return report

async def main():
    print("==================================================")
    print("   Running Comprehensive Evaluation of All TCs    ")
    print("==================================================")
    
    results = []
    for tc in TEST_SUITE.test_cases:
        print(f"\n[RUNNING] {tc.id}: {tc.name}...")
        res = await run_single_test(tc)
        results.append(res)
        print(f"[STATUS] {tc.id} -> {res['status']}")
        if res["error"]:
            print(f"  Note/Error: {res['error']}")
            
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print("\nSaved report to evaluation_report.json")

if __name__ == "__main__":
    asyncio.run(main())
