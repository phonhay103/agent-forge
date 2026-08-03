import json
import logging
import pathlib
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from prompt_composer import PromptComposer

from src.dynamic_agent.models import DynamicPlan, DynamicPlanTask
from src.shared.mcp_protocols import MCPSessionProtocol
from src.shared.executor_models import ExecutionContext
from src.shared.llm_client import run_structured_llm

logger = logging.getLogger("dynamic_agent")
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


class DynamicExecutor:
    """
    Executor that uses LLM to bind output->input between tasks
    based on schema matching. No variable expressions needed.
    """

    def __init__(
        self,
        session: MCPSessionProtocol,
        model: Optional[Any] = None,
        model_name: str = "gemini-2.5-flash",
        prompt: Optional[PromptComposer] = None,
    ):
        self.session = session
        self.model_name = model_name
        if model is None:
            from src.shared.llm_client import get_llm_client
            model = get_llm_client(model_name)
        self.model = model
        self.prompt = prompt

    async def run_plan(self, plan: DynamicPlan) -> ExecutionContext:
        ctx = ExecutionContext()

        tools_res = await self.session.list_tools()
        tools_list = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        tools_map = {t.name: t for t in tools_list}

        for task in plan.tasks:
            logger.info(f"Executing task '{task.id}' using tool '{task.tool_name}'...")

            target_tool = tools_map.get(task.tool_name)
            target_input_schema = target_tool.input_schema if target_tool else {}

            # Collect outputs from dependent tasks
            dependency_context = {
                dep_id: ctx.store[dep_id]
                for dep_id in task.depends_on
                if dep_id in ctx.store
            }

            # Use LLM to generate tool arguments from context + target schema
            resolved_args = self._llm_bind(
                tool_name=task.tool_name,
                input_schema=target_input_schema,
                input_description=task.input_description,
                dependency_context=dependency_context,
            )

            # Auto-wrap in {"input": ...} if target schema expects it
            if target_input_schema and "input" in target_input_schema.get("properties", {}):
                if isinstance(resolved_args, dict) and "input" not in resolved_args:
                    resolved_args = {"input": resolved_args}

            logger.debug(f"Resolved args for '{task.tool_name}': {resolved_args}")

            result = await self.session.call_tool(
                name=task.tool_name,
                arguments=resolved_args,
            )
            content = result.content[0].text
            try:
                parsed_output = json.loads(content)
            except Exception:
                parsed_output = content

            logger.info(f"Task [{task.id}] succeeded.")
            ctx.add_result(task.id, task.tool_name, parsed_output)

        logger.info("Dynamic plan execution completed.")
        return ctx

    def _llm_bind(
        self,
        tool_name: str,
        input_schema: dict,
        input_description: str,
        dependency_context: dict,
    ) -> dict:
        """Use LLM to generate tool arguments by matching schemas."""
        prompt = self.prompt or PromptComposer.from_file("dynamic_bind_prompt.yaml", PROMPTS_DIR)
        prompt.set_variables({
            "tool_name": tool_name,
            "target_schema": json.dumps(input_schema, indent=2),
            "input_description": input_description,
            "context_data": json.dumps(dependency_context, indent=2, default=str),
        })
        prompt_text = prompt.render()

        result = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={},
            schema=input_schema,
            model_name=self.model_name,
            base_model=self.model,
        )

        if isinstance(result, BaseModel):
            return result.model_dump()
        return result
