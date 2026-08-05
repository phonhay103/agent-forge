import asyncio
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from src.agent.planner import UnifiedPlanner
from src.agent.models import UnifiedPlan, DynamicBindingMode
from src.agent.executor import UnifiedExecutor
from src.agent.plan_display import format_plan_display
from src.shared.mcp_protocols import MCPClient
from src.shared.test_inputs import TEST_SUITE
from src.shared.executor_models import ExecutionContext

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")

def format_exception(e: BaseException) -> str:
    """Recursively extract human-readable error messages from ExceptionGroup or Exception."""
    if isinstance(e, BaseExceptionGroup):
        return "\n".join(format_exception(sub) for sub in e.exceptions)
    return f"{type(e).__name__}: {e}"


async def run_unified_agent(dynamic_binding_mode: Optional[DynamicBindingMode], mode_title: str):
    load_dotenv()

    print("==================================================")
    print(f"      Unified Agent: {mode_title} Mode            ")
    print("==================================================")
    print(f"Server URL: {MCP_SERVER_URL}\n")

    print("--- Available Test Cases ---")
    for idx, tc in enumerate(TEST_SUITE.test_cases, 1):
        print(f"[{idx}] {tc.id} ({tc.category.upper()}): {tc.name}")
        print(f"    Prompt: {tc.query}")
    print("[0] Custom Input\n")

    choice = input("Select a test case number (0 to enter custom input): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(TEST_SUITE.test_cases):
        selected_tc = TEST_SUITE.test_cases[int(choice) - 1]
        task = selected_tc.query
        print(f"\nRunning Test Case: {selected_tc.id} - {selected_tc.name}")
        print(f"Query: {task}\n")
    else:
        task = input("Enter your custom task: ").strip()

    binding_type = "jmespath"
    enable_llm_fallback = False

    # Static mode check
    if dynamic_binding_mode is None:
        # Ask for binding engine only in static mode
        print("\n--- Select Variable Binding Engine ---")
        print("[1] JMESPath (with Automatic LLM Direct Mapping Fallback)")
        print("[2] JSONPath (with Automatic LLM Direct Mapping Fallback)")
        print("[3] Dot Notation (with Automatic LLM Direct Mapping Fallback)")
        engine_choice = input("Select binding engine [1-3] (default 1): ").strip()
        if engine_choice == "2":
            binding_type = "jsonpath"
        elif engine_choice == "3":
            binding_type = "dot_notation"
        
        fallback_choice = input("Enable Automatic LLM Direct Mapping Fallback? [y/N] (default No): ").strip().lower()
        enable_llm_fallback = fallback_choice in ("y", "yes", "true", "1")
        print(f"Selected Binding Engine: {binding_type.upper()} (LLM Fallback Enabled: {enable_llm_fallback})\n")

    print(f"\n--- Connecting to MCP Server at {MCP_SERVER_URL} ---")
    
    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                print("--- Discovering Tools via MCP Server ---")
                await session.initialize()
                tools_list = await session.list_tools()
                tools_metadata = [t.model_dump() for t in tools_list.tools]
                print(f"Discovered {len(tools_metadata)} tools from MCP server.\n")

                try:
                    # Only validate expected schemas in JMESPATH_VALIDATE mode
                    use_pre_planned = (dynamic_binding_mode == DynamicBindingMode.JMESPATH_VALIDATE)
                    planner = UnifiedPlanner(use_pre_planned_jmespath=use_pre_planned)
                    plan: UnifiedPlan = planner.create_plan(
                        task,
                        tools_metadata,
                        binding_type=binding_type,
                        enable_llm_fallback=enable_llm_fallback
                    )
                except Exception as plan_err:
                    print(f"\n[PLANNING ERROR] Failed to create plan: {format_exception(plan_err)}")
                    return

                print(format_plan_display(
                    plan,
                    tools_metadata,
                    binding_type=binding_type,
                    enable_llm_fallback=enable_llm_fallback
                ))
                print()

                mcp_client = MCPClient(session)
                executor = UnifiedExecutor(
                    mcp_client,
                    dynamic_binding_mode=dynamic_binding_mode,
                    binding_engine=binding_type,
                    enable_llm_fallback=enable_llm_fallback
                )
                try:
                    results: ExecutionContext = await executor.run_plan(plan)
                    print("\n--- Final Execution Results (Pydantic ExecutionContext) ---")
                    print(results.model_dump_json(indent=2))
                except ValueError as ve:
                    print(f"\n[EXECUTION HALTED] {ve}")
                except Exception as ex:
                    print(f"\n[EXECUTION ERROR] {format_exception(ex)}")
    except (ConnectionError, OSError) as conn_err:
        print(f"\nError: Could not connect to MCP Server at {MCP_SERVER_URL}: {format_exception(conn_err)}")
        print("Please ensure the MCP server is running independently ('make server' or 'uv run python -m src.mcp.server').")
        sys.exit(1)
    except Exception as general_err:
        err_msg = format_exception(general_err)
        if "connect" in err_msg.lower() or "refused" in err_msg.lower() or "404" in err_msg.lower():
            print(f"\nError: Could not connect to MCP Server at {MCP_SERVER_URL}: {err_msg}")
            print("Please ensure the MCP server is running independently ('make server' or 'uv run python -m src.mcp.server').")
        else:
            print(f"\n[AGENT ERROR] {err_msg}")
        sys.exit(1)


async def main_static():
    await run_unified_agent(
        dynamic_binding_mode=None,
        mode_title="Static Binding"
    )


async def main_dynamic():
    print("\n--- Select Dynamic Binding Mode ---")
    print("[1] JMESPath with Validation (validate expected schemas)")
    print("[2] JMESPath with LLM (re-bind using LLM)")
    print("[3] LLM Direct (direct mapping using LLM)")
    choice = input("Select [1-3] (default 1): ").strip()
    
    if choice == "2":
        mode = DynamicBindingMode.JMESPATH_LLM
    elif choice == "3":
        mode = DynamicBindingMode.LLM_DIRECT
    else:
        mode = DynamicBindingMode.JMESPATH_VALIDATE
        
    await run_unified_agent(
        dynamic_binding_mode=mode,
        mode_title=f"Dynamic ({mode.value})"
    )


async def main():
    print("Select Mode:")
    print("[1] Static Binding Mode")
    print("[2] Dynamic Schema-Match Mode")
    choice = input("Choice: ").strip()
    if choice == "2":
        await main_dynamic()
    else:
        await main_static()


if __name__ == "__main__":
    asyncio.run(main())
