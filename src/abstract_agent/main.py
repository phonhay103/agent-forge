"""
Abstract Planning Agent — Interactive CLI
Run: python -m src.abstract_agent
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client

from mcp import ClientSession
from src.abstract_agent.executor import AbstractExecutor
from src.abstract_agent.models import AbstractPlan
from src.abstract_agent.plan_display import format_plan_display
from src.abstract_agent.planner import AbstractPlanner
from src.shared.executor_models import ExecutionContext
from src.shared.mcp_protocols import MCPClient
from src.shared.test_inputs import TEST_SUITE

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")


def format_exception(e: BaseException) -> str:
    """Recursively extract human-readable error messages from ExceptionGroup or Exception."""
    if isinstance(e, BaseExceptionGroup):
        return "\n".join(format_exception(sub) for sub in e.exceptions)
    return f"{type(e).__name__}: {e}"


async def main() -> None:
    load_dotenv()

    print("==================================================")
    print("      Abstract Planning Agent (LLM Full Runtime)  ")
    print("==================================================")
    print(f"Server URL: {MCP_SERVER_URL}\n")

    print("--- Available Test Cases ---")
    for idx, tc in enumerate(TEST_SUITE.test_cases, 1):
        print(f"[{idx}] {tc.id} ({tc.category.upper()}): {tc.name}")
        print(f"    Prompt: {tc.query}")
    print("[0] Custom Input\n")

    choice = input("Select a test case number (0 for custom): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(TEST_SUITE.test_cases):
        selected_tc = TEST_SUITE.test_cases[int(choice) - 1]
        task = selected_tc.query
        print(f"\nRunning: {selected_tc.id} - {selected_tc.name}")
        print(f"Query: {task}\n")
    else:
        task = input("Enter your custom task: ").strip()

    print(f"\n--- Connecting to MCP Server at {MCP_SERVER_URL} ---")

    try:
        async with (
            streamablehttp_client(MCP_SERVER_URL) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            print("--- Discovering Tools via MCP Server ---")
            await session.initialize()
            tools_list = await session.list_tools()
            tools_metadata = [t.model_dump() for t in tools_list.tools]
            print(f"Discovered {len(tools_metadata)} tools.\n")

            try:
                planner = AbstractPlanner()
                plan: AbstractPlan = planner.create_plan(task, tools_metadata)
            except Exception as plan_err:
                print(f"\n[PLANNING ERROR] Failed to create plan: {format_exception(plan_err)}")
                return

            print(format_plan_display(plan, tools_metadata))
            print()

            mcp_client = MCPClient(session)
            executor = AbstractExecutor(mcp_client)
            try:
                results: ExecutionContext = await executor.run_plan(plan)
                print("\n--- Final Execution Results ---")
                print(results.model_dump_json(indent=2))
            except ValueError as ve:
                print(f"\n[EXECUTION HALTED] {ve}")
            except Exception as ex:
                print(f"\n[EXECUTION ERROR] {format_exception(ex)}")
    except (ConnectionError, OSError) as conn_err:
        print(f"\nError: Could not connect to MCP Server at {MCP_SERVER_URL}: {format_exception(conn_err)}")
        print("Please ensure the MCP server is running.")
        sys.exit(1)
    except Exception as general_err:
        err_msg = format_exception(general_err)
        if "connect" in err_msg.lower() or "refused" in err_msg.lower() or "404" in err_msg.lower():
            print(f"\nError: Could not connect to MCP Server at {MCP_SERVER_URL}: {err_msg}")
        else:
            print(f"\n[AGENT ERROR] {err_msg}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
