"""
MCP Multi-Agent System — Unified CLI
Run: python -m src.main  OR  make agent
"""
import asyncio


async def main() -> None:
    print("==================================================")
    print("      MCP Multi-Agent System                      ")
    print("==================================================")
    print()
    print("--- Select Agent Type ---")
    print("[1] Static Binding Agent  (deterministic JMESPath/JSONPath/Dot)")
    print("[2] Dynamic Binding Agent (LLM schema-match at runtime)")
    print("[3] Abstract Planning Agent (LLM resolves tools + data)")
    print()
    choice = input("Select [1-3] (default 1): ").strip()

    if choice == "2":
        from src.agent.main import main_dynamic as agent_main
    elif choice == "3":
        from src.abstract_agent.main import main as agent_main
    else:
        from src.agent.main import main_static as agent_main

    await agent_main()


if __name__ == "__main__":
    asyncio.run(main())
