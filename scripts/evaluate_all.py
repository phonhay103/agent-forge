import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure repo root is in sys.path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from src.agent.planner import Planner
from src.agent.models import Plan
from src.agent.executor import StaticExecutor as HeadlessExecutor
from src.shared.executor_models import ExecutionContext
from src.shared.mcp_protocols import MCPClient
from src.shared.test_inputs import TEST_SUITE, TestCase
from src.agent.main import MCP_SERVER_URL

load_dotenv()


def format_exception(e: BaseException) -> str:
    if isinstance(e, BaseExceptionGroup):
        return "\n".join(format_exception(sub) for sub in e.exceptions)
    return f"{type(e).__name__}: {e}"


async def run_single_test(
    tc: TestCase,
    binding_type: str = "jmespath",
) -> dict:
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
                
                try:
                    planner = Planner()
                    plan: Plan = planner.create_plan(
                        tc.query,
                        tools_metadata,
                        binding_type=binding_type,
                    )
                    report["plan"] = plan.model_dump()
                except Exception as plan_err:
                    report["status"] = "PLANNING_ERROR"
                    report["error"] = format_exception(plan_err)
                    return report
                
                mcp_client = MCPClient(session)
                executor = HeadlessExecutor(
                    mcp_client,
                    binding_engine=binding_type,
                )
                
                try:
                    results: ExecutionContext = await executor.run_plan(plan)
                    report["execution"] = results.model_dump()
                    report["status"] = "PASSED"
                except ValueError as ve:
                    report["status"] = "HALTED_BY_DESIGN" if ("__BINDING_FAILED_TOKEN" in str(ve) or "Execution Halted" in str(ve)) else "FAILED"
                    report["error"] = str(ve)
                except Exception as e:
                    report["status"] = "FAILED"
                    report["error"] = format_exception(e)
    except Exception as outer_e:
        err_msg = format_exception(outer_e)
        if "connect" in err_msg.lower() or "refused" in err_msg.lower():
            report["status"] = "SERVER_ERROR"
        else:
            report["status"] = "ERROR"
        report["error"] = err_msg
                
    return report


async def main():
    parser = argparse.ArgumentParser(description="Run Evaluation Suite for MCP Headless Core.")
    parser.add_argument(
        "--engine", "-e",
        choices=["jmespath", "jsonpath", "dot_notation"],
        default="jmespath",
        help="Variable binding engine to evaluate (default: jmespath)"
    )

    parser.add_argument(
        "--tc", "-t",
        type=str,
        default=None,
        help="Run a specific test case by ID (e.g., TC-01)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="evaluation_report.json",
        help="Output report JSON file path (default: evaluation_report.json)"
    )
    args = parser.parse_args()

    print("==================================================")
    print("   Running Comprehensive Evaluation Suite         ")
    print(f"   Engine: {args.engine.upper()}")
    print("==================================================")

    test_cases = TEST_SUITE.test_cases
    if args.tc:
        test_cases = [tc for tc in test_cases if tc.id.upper() == args.tc.upper()]
        if not test_cases:
            print(f"Error: Test case with ID '{args.tc}' not found.")
            sys.exit(1)

    results = []
    for tc in test_cases:
        print(f"\n[RUNNING] {tc.id}: {tc.name}...")
        res = await run_single_test(tc, binding_type=args.engine)
        results.append(res)
        print(f"[STATUS] {tc.id} -> {res['status']}")
        if res["error"]:
            print(f"  Note/Error: {res['error']}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Print Summary Table
    print("\n" + "=" * 60)
    print("                EVALUATION SUMMARY RESULTS                 ")
    print("=" * 60)
    passed = sum(1 for r in results if r['status'] == 'PASSED')
    halted = sum(1 for r in results if r['status'] == 'HALTED_BY_DESIGN')
    failed = sum(1 for r in results if r['status'] in ('FAILED', 'SERVER_ERROR'))
    
    print(f"Total Evaluated: {len(results)}")
    print(f"PASSED:           {passed} ({passed / len(results) * 100:.1f}%)")
    print(f"HALTED_BY_DESIGN: {halted} ({halted / len(results) * 100:.1f}%)")
    print(f"FAILED/ERROR:     {failed} ({failed / len(results) * 100:.1f}%)")
    print(f"Report saved to:  {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
