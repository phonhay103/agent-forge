import json
import logging
import pathlib
from typing import Any

from pydantic import BaseModel, Field

from prompt_composer import PromptComposer
from src.abstract_agent.models import AbstractPlan
from src.shared.executor_models import ExecutionContext
from src.shared.llm_client import run_structured_llm
from src.shared.mcp_protocols import MCPSessionProtocol

logger = logging.getLogger("abstract_agent")
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"

TOOL_SELECTION_CONFIDENCE_THRESHOLD = 0.6


class ToolSelection(BaseModel):
    """LLM output for tool resolution."""
    tool_name: str = Field(description="Name of the selected tool")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    reasoning: str = Field(description="Why this tool was selected")


class AbstractExecutor:
    """
    Executor that resolves both tool selection AND data binding at runtime.
    Plan tasks only contain intents.
    """

    def __init__(
        self,
        session: MCPSessionProtocol,
        model: Any | None = None,
        model_name: str = "gemini-2.5-flash",
        tool_resolver_prompt: PromptComposer | None = None,
        bind_prompt: PromptComposer | None = None,
    ):
        self.session = session
        self.model_name = model_name
        if model is None:
            from src.shared.llm_client import get_llm_client
            model = get_llm_client(model_name)
        self.model = model
        self.tool_resolver_prompt = tool_resolver_prompt
        self.bind_prompt = bind_prompt

    async def run_plan(self, plan: AbstractPlan) -> ExecutionContext:
        ctx = ExecutionContext()

        tools_res = await self.session.list_tools()
        tools_list = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        tools_map = {t.name: t for t in tools_list}
        tools_metadata = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
            }
            for t in tools_list
        ]

        for task in plan.tasks:
            logger.info(f"Executing task '{task.id}': {task.intent}")

            dependency_context = {
                dep_id: ctx.store[dep_id]
                for dep_id in task.depends_on
                if dep_id in ctx.store
            }

            # Step 1: Resolve intent -> tool selection
            tool_selection = self._resolve_tool(
                intent=task.intent,
                expected_input=task.expected_input,
                expected_output=task.expected_output,
                available_tools=tools_metadata,
            )

            if tool_selection.confidence < TOOL_SELECTION_CONFIDENCE_THRESHOLD:
                raise ValueError(
                    f"Tool selection confidence too low for task '{task.id}': "
                    f"selected '{tool_selection.tool_name}' with confidence {tool_selection.confidence:.2f} "
                    f"(threshold: {TOOL_SELECTION_CONFIDENCE_THRESHOLD}). "
                    f"Reasoning: {tool_selection.reasoning}"
                )

            selected_tool_name = tool_selection.tool_name
            logger.info(
                f"Task [{task.id}] resolved to tool '{selected_tool_name}' "
                f"(confidence: {tool_selection.confidence:.2f})"
            )

            target_tool = tools_map.get(selected_tool_name)
            target_input_schema = target_tool.input_schema if target_tool else {}

            # Step 2: LLM generates arguments
            resolved_args = self._llm_bind(
                tool_name=selected_tool_name,
                input_schema=target_input_schema,
                intent=task.intent,
                expected_input=task.expected_input,
                dependency_context=dependency_context,
            )

            # Auto-wrap in {"input": ...} if needed
            if target_input_schema and "input" in target_input_schema.get("properties", {}):
                if isinstance(resolved_args, dict) and "input" not in resolved_args:
                    resolved_args = {"input": resolved_args}

            result = await self.session.call_tool(
                name=selected_tool_name,
                arguments=resolved_args,
            )
            content = result.content[0].text
            try:
                parsed_output = json.loads(content)
            except Exception:
                parsed_output = content

            logger.info(f"Task [{task.id}] succeeded via tool '{selected_tool_name}'.")
            ctx.add_result(task.id, selected_tool_name, parsed_output)

        logger.info("Abstract plan execution completed.")
        return ctx

    def _resolve_tool(
        self,
        intent: str,
        expected_input: str | None,
        expected_output: str | None,
        available_tools: list[dict],
    ) -> ToolSelection:
        """Use LLM to match intent to the best available tool."""
        prompt = self.tool_resolver_prompt or PromptComposer.from_file("tool_resolver_prompt.yaml", PROMPTS_DIR)
        prompt.set_variables({
            "intent": intent,
            "expected_input": expected_input or "N/A",
            "expected_output": expected_output or "N/A",
            "available_tools": json.dumps(available_tools, indent=2),
        })
        prompt_text = prompt.render()

        result = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={},
            schema=ToolSelection,
            model_name=self.model_name,
            base_model=self.model,
        )
        return result

    def _llm_bind(
        self,
        tool_name: str,
        input_schema: dict,
        intent: str,
        expected_input: str | None,
        dependency_context: dict,
    ) -> dict:
        """Use LLM to generate tool arguments."""
        prompt = self.bind_prompt or PromptComposer.from_file("abstract_bind_prompt.yaml", PROMPTS_DIR)
        prompt.set_variables({
            "tool_name": tool_name,
            "target_schema": json.dumps(input_schema, indent=2),
            "intent": intent,
            "expected_input": expected_input or "N/A",
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
