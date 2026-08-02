import json
import logging
from typing import Any, List, Dict, Union, Optional
from pydantic import BaseModel, Field

from src.core.planner.planner import Plan, PlanStep
from json_schema_binder import (
    BaseBindingEngine,
    get_binding_engine,
    LLMFallbackMapper,
    VariableParser,
    resolve_variables,
    BindingContext,
)
from src.core.engine.protocols import MCPSessionProtocol

import os

logger = logging.getLogger("headless_core")

DEFAULT_BINDING_FAILED_TOKEN = os.getenv("BINDING_FAILED_TOKEN", "__BINDING_FAILED__")

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
        model: Optional[Any] = None,
        binding_failed_token: Optional[str] = None
    ):
        self.session = session
        if isinstance(binding_engine, str):
            self.binding_engine = get_binding_engine(binding_engine)
        else:
            self.binding_engine = binding_engine
        
        self.enable_llm_fallback = enable_llm_fallback
        self.binding_failed_token = binding_failed_token or DEFAULT_BINDING_FAILED_TOKEN
        self.step_schemas_store: Dict[str, Any] = {}
        
        if self.enable_llm_fallback:
            if model is None:
                from src.core.llm_client import get_llm_client
                model = get_llm_client()
            self.model = model
            self.fallback_mapper = LLMFallbackMapper(model=self.model)
            logger.info("HeadlessExecutor initialized with automatic LLM Fallback mapping.")
        else:
            self.model = model
            self.fallback_mapper = None
            logger.info("HeadlessExecutor initialized with strict deterministic variable binding.")

    def _resolve_variables(
        self,
        args: Any,
        store: Dict[str, Any],
        target_tool_input_schema: Optional[Dict[str, Any]] = None,
        step_schemas_store: Optional[Dict[str, Any]] = None,
        enable_llm_fallback: bool = False,
        directive: Optional[str] = None
    ) -> Any:
        context = BindingContext.from_dict(store)
        if step_schemas_store:
            context.metadata.update(step_schemas_store)

        fallback = self.fallback_mapper if enable_llm_fallback else None

        if enable_llm_fallback and fallback:
            from json_schema_binder import TemplateResolver, VariableParser
            resolver = TemplateResolver(engine=self.binding_engine)
            partially_resolved = resolver.resolve_payload(args, context)
            if VariableParser.has_unresolved_references(partially_resolved):
                unresolved = VariableParser.extract_unresolved_references(partially_resolved)
                msg = (
                    f"⚠️ [LLM FALLBACK TRIGGERED]\n"
                    f"   Primary engine '{self.binding_engine.binding_type.value}' failed for references: {unresolved}\n"
                    f"   Directive: {directive or 'N/A'}\n"
                    f"   Invoking LLM Fallback Mapper to repair payload..."
                )
                logger.warning(msg)
                print(f"\n{msg}\n", flush=True)

        return resolve_variables(
            payload=args,
            context=context,
            engine=self.binding_engine,
            target_schema=target_tool_input_schema,
            fallback_mapper=fallback,
            directive=directive
        )

    async def run_plan(self, plan: Plan) -> ExecutionContext:
        ctx = ExecutionContext()
        logger.info(f"Starting execution of plan containing {len(plan.steps)} steps.")
        
        tools_res = await self.session.list_tools()
        tools_list = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        tools_map = {t.name: t for t in tools_list}

        for step in plan.steps:
            logger.info(f"Executing step '{step.id}' using tool '{step.tool_name}'...")
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
            
            failed_token = self.binding_failed_token

            def find_unresolved_issue(v: Any) -> Optional[str]:
                if v == failed_token:
                    return f"Sent by Planner due to missing input data ('{failed_token}')"
                if VariableParser.is_variable_reference(v):
                    return f"Failed to evaluate expression '{v}'"
                if isinstance(v, dict):
                    for val in v.values():
                        res = find_unresolved_issue(val)
                        if res:
                            return res
                if isinstance(v, list):
                    for val in v:
                        res = find_unresolved_issue(val)
                        if res:
                            return res
                return None

            issue = find_unresolved_issue(resolved_args)
            if issue:
                err_msg = (
                    f"Execution Halted: Variable binding failed for step '{step.id}' "
                    f"using engine '{self.binding_engine.binding_type.value}'. "
                    f"Reason: {issue}."
                )
                logger.error(err_msg)
                raise ValueError(err_msg)
            # Ensure args are dict format for MCP call_tool
            if isinstance(resolved_args, BaseModel):
                call_args = resolved_args.model_dump()
            elif isinstance(resolved_args, dict):
                call_args = resolved_args.copy()
            else:
                call_args = resolved_args

            # Auto-wrap in {"input": ...} if the target tool expects an "input" key and call_args doesn't have it
            if target_tool_input_schema and "input" in target_tool_input_schema.get("properties", {}):
                if isinstance(call_args, dict) and "input" not in call_args:
                    call_args = {"input": call_args}

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
