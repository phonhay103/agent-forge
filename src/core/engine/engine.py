import json
import logging
from typing import Any, List, Dict, Union, Optional
from pydantic import BaseModel, Field

from src.core.planner.planner import Plan, PlanStep
from src.core.binding import BaseBindingEngine, get_binding_engine
from src.core.binding.llm_fallback import LLMFallbackMapper
from src.core.engine.protocols import MCPSessionProtocol
from src.core.engine.parser import VariableParser

logger = logging.getLogger("headless_core")

class StepResult(BaseModel):
    step_id: str
    tool_name: str
    output: Any

class ExecutionContext(BaseModel):
    results: List[StepResult] = Field(default_factory=list)
    store: Dict[str, Any] = Field(default_factory=dict)

    def add_result(self, step_id: str, tool_name: str, output: Any):
        self.results.append(StepResult(step_id=step_id, tool_name=tool_name, output=output))
        self.store[step_id] = output

class HeadlessExecutor:
    def __init__(
        self,
        session: MCPSessionProtocol,
        binding_engine: Union[str, BaseBindingEngine] = "jmespath",
        enable_llm_fallback: bool = False,
        model: Optional[Any] = None
    ):
        self.session = session
        if isinstance(binding_engine, str):
            self.binding_engine = get_binding_engine(binding_engine)
        else:
            self.binding_engine = binding_engine
        
        self.enable_llm_fallback = enable_llm_fallback
        self.step_schemas_store = {}
        if self.enable_llm_fallback:
            self.fallback_mapper = LLMFallbackMapper(model=model)
            logger.info("HeadlessExecutor initialized with automatic LLM Fallback mapping.")
        else:
            logger.info("HeadlessExecutor initialized with strict deterministic variable binding.")

    def _resolve_variables(
        self,
        val: Any,
        context_store: Dict[str, Any],
        target_tool_input_schema: Any = None,
        step_schemas_store: Any = None,
        enable_llm_fallback: bool = False,
        directive: Any = None
    ) -> Any:
        """
        Delegates variable resolution to the configured independent binding engine
        (e.g. JMESPath, JSONPath, Dot Notation, or LLM Natural Language Directive).
        """
        resolved = self.binding_engine.resolve(
            val,
            context_store,
            target_tool_input_schema=target_tool_input_schema,
            step_schemas_store=step_schemas_store,
        )

        if enable_llm_fallback and target_tool_input_schema and VariableParser.has_unresolved_references(resolved):
            logger.warning(
                "Deterministic binding left unresolved references in arguments. "
                "Triggering LLM Fallback Mapper..."
            )
            resolved = self.fallback_mapper.repair_arguments(
                context_store=context_store,
                target_tool_input_schema=target_tool_input_schema,
                partially_resolved_args=resolved,
                directive=directive
            )
            logger.info("LLM Fallback Mapper repair complete.")

        return resolved

    async def run_plan(self, plan: Plan) -> ExecutionContext:
        ctx = ExecutionContext()
        logger.info(f"Starting execution of plan containing {len(plan.steps)} steps.")
        
        # Fetch tool definitions exactly once to avoid repetitive list_tools network calls
        tools_list = await self.session.list_tools()
        tools_map = {t.name: t for t in tools_list}

        for step in plan.steps:
            target_tool_metadata = tools_map.get(step.tool_name)
            target_tool_input_schema = target_tool_metadata.input_schema if target_tool_metadata else {}
            # Resolve references to previous step outputs with tool schema context
            resolved_args = self._resolve_variables(
                step.args,
                ctx.store,
                target_tool_input_schema=target_tool_input_schema,
                step_schemas_store=self.step_schemas_store,
                enable_llm_fallback=self.enable_llm_fallback,
                directive=getattr(step, "directive", None)
            )
            
            # Ensure args are dict format for MCP call_tool
            if isinstance(resolved_args, BaseModel):
                call_args = resolved_args.model_dump()
            elif isinstance(resolved_args, dict):
                call_args = resolved_args
            else:
                call_args = {"input": resolved_args}

            logger.debug(f"Resolved call arguments for tool '{step.tool_name}': {call_args}")

            result = await self.session.call_tool(
                name=step.tool_name, 
                arguments=call_args
            )
            
            content = result.content[0].text
            try:
                parsed_output = json.loads(content)
            except Exception:
                parsed_output = content
            
            logger.info(f"Step [{step.id}] execution succeeded. Output stored in context.")
            ctx.add_result(step.id, step.tool_name, parsed_output)
            
            # Record source step tool schemas
            self.step_schemas_store[step.id] = {
                "tool_name": step.tool_name,
                "input_schema": target_tool_input_schema,
                "output_schema": target_tool_metadata.output_schema if target_tool_metadata else {}
            }
            
        logger.info("Execution of plan completed successfully.")
        return ctx
