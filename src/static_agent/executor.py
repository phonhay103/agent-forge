import json
import logging
from typing import Any, List, Dict, Union, Optional
from pydantic import BaseModel, Field

from src.static_agent.models import Plan, PlanTask
from json_schema_binder import (
    BaseBindingEngine,
    get_binding_engine,
    LLMFallbackMapper,
    VariableParser,
    resolve_variables,
    BindingContext,
)
from src.shared.mcp_protocols import MCPSessionProtocol
from src.shared.executor_models import ExecutionContext
from src.shared.llm_client import get_llm_client
import os
import re

logger = logging.getLogger("headless_core")

def _extract_task_references(args: Any) -> set:
    refs = set()
    if isinstance(args, str):
        for match in re.findall(r'\$task_[a-zA-Z0-9_]+', args):
            refs.add(match)
    elif isinstance(args, dict):
        for v in args.values():
            refs.update(_extract_task_references(v))
    elif isinstance(args, list):
        for item in args:
            refs.update(_extract_task_references(item))
    return refs

def _rename_task_references(args: Any, id_map: Dict[str, str]) -> Any:
    if isinstance(args, str):
        for old, new in id_map.items():
            args = re.sub(r'\$' + re.escape(old) + r'\b', '$' + new, args)
        return args
    elif isinstance(args, dict):
        return {k: _rename_task_references(v, id_map) for k, v in args.items()}
    elif isinstance(args, list):
        return [_rename_task_references(v, id_map) for v in args]
    return args

DEFAULT_BINDING_FAILED_TOKEN = os.getenv("BINDING_FAILED_TOKEN", "__BINDING_FAILED__")

class StaticExecutor:
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
        self.task_schemas_store: Dict[str, Any] = {}
        
        if self.enable_llm_fallback:
            if model is None:
                model = get_llm_client()
            self.model = model
            self.fallback_mapper = LLMFallbackMapper(model=self.model)
            logger.info("StaticExecutor initialized with automatic LLM Fallback mapping.")
        else:
            self.model = model
            self.fallback_mapper = None
            logger.info("StaticExecutor initialized with strict deterministic variable binding.")

    def _resolve_variables(
        self,
        args: Any,
        store: Dict[str, Any],
        target_tool_input_schema: Optional[Dict[str, Any]] = None,
        task_schemas_store: Optional[Dict[str, Any]] = None,
        enable_llm_fallback: bool = False,
        directive: Optional[str] = None
    ) -> Any:
        context = BindingContext.from_dict(store)
        if task_schemas_store:
            context.metadata.update(task_schemas_store)

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
        logger.info(f"Starting execution of plan containing {len(plan.tasks)} tasks.")

        # Resolve any mismatched task reference names dynamically
        actual_ids = [t.id for t in plan.tasks]
        id_map = {}
        for idx, task in enumerate(plan.tasks):
            refs = _extract_task_references(task.args)
            for ref in refs:
                ref_name = ref.lstrip("$")
                if ref_name not in actual_ids:
                    # Look for the best candidate from previous tasks
                    candidates = [aid for aid in actual_ids[:idx] if aid in ref_name or ref_name in aid]
                    if not candidates:
                        # Fallback: if only one task has executed before, map to it
                        if idx == 1:
                            candidates = [plan.tasks[0].id]
                    if candidates:
                        id_map[ref_name] = candidates[0]

        if id_map:
            logger.info(f"Fuzzy matching mismatched task references: {id_map}")
            for task in plan.tasks:
                task.args = _rename_task_references(task.args, id_map)
        
        tools_res = await self.session.list_tools()
        tools_list = tools_res.tools if hasattr(tools_res, "tools") else tools_res
        tools_map = {t.name: t for t in tools_list}

        for task in plan.tasks:
            logger.info(f"Executing task '{task.id}' using tool '{task.tool_name}'...")
            target_tool_metadata = tools_map.get(task.tool_name)
            target_tool_input_schema = target_tool_metadata.input_schema if target_tool_metadata else {}
            # Resolve references to previous task outputs with tool schema context
            resolved_args = self._resolve_variables(
                task.args,
                ctx.store,
                target_tool_input_schema=target_tool_input_schema,
                task_schemas_store=self.task_schemas_store,
                enable_llm_fallback=self.enable_llm_fallback,
                directive=getattr(task, "directive", None)
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
                    f"Execution Halted: Variable binding failed for task '{task.id}' "
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

            logger.debug(f"Resolved call arguments for tool '{task.tool_name}': {call_args}")

            result = await self.session.call_tool(
                name=task.tool_name, 
                arguments=call_args
            )
            
            content = result.content[0].text
            try:
                parsed_output = json.loads(content)
            except Exception:
                parsed_output = content
            
            logger.info(f"Task [{task.id}] execution succeeded. Output stored in context.")
            ctx.add_result(task.id, task.tool_name, parsed_output)
            
            # Record source task tool schemas
            self.task_schemas_store[task.id] = {
                "tool_name": task.tool_name,
                "input_schema": target_tool_input_schema,
                "output_schema": target_tool_metadata.output_schema if target_tool_metadata else {}
            }
            
        logger.info("Execution of plan completed successfully.")
        return ctx
