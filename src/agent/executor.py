import json
import logging
import os
import pathlib
import re
from typing import Any

from json_schema_binder import (
    BaseBindingEngine,
    BindingContext,
    VariableParser,
    get_binding_engine,
    resolve_variables,
)
from prompt_composer import PromptComposer
from src.agent.binder import DynamicDataBinder
from src.agent.models import DynamicBindingMode, DynamicPlan, StaticPlan, UnifiedPlan
from src.shared.executor_models import ExecutionContext
from src.shared.mcp_protocols import MCPSessionProtocol

logger = logging.getLogger("executor")
DEFAULT_BINDING_FAILED_TOKEN = os.getenv("BINDING_FAILED_TOKEN", "__BINDING_FAILED__")
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


def _extract_task_references(args: Any) -> set[str]:
    refs = set()
    if isinstance(args, str):
        for match in re.findall(r"\$task_[a-zA-Z0-9_]+", args):
            refs.add(match)
    elif isinstance(args, dict):
        for v in args.values():
            refs.update(_extract_task_references(v))
    elif isinstance(args, list):
        for item in args:
            refs.update(_extract_task_references(item))
    return refs


def _rename_task_references(args: Any, id_map: dict[str, str]) -> Any:
    if isinstance(args, str):
        for old, new in id_map.items():
            args = re.sub(r"\$" + re.escape(old) + r"\b", "$" + new, args)
        return args
    elif isinstance(args, dict):
        return {k: _rename_task_references(v, id_map) for k, v in args.items()}
    elif isinstance(args, list):
        return [_rename_task_references(v, id_map) for v in args]
    return args


class StaticExecutor:
    def __init__(
        self,
        session: MCPSessionProtocol,
        binding_engine: str | BaseBindingEngine = "jmespath",
        model: Any | None = None,
        binding_failed_token: str | None = None,
    ) -> None:
        self.session = session
        self.binding_failed_token = binding_failed_token or DEFAULT_BINDING_FAILED_TOKEN

        from src.agent.planner import StaticPlanner

        self.planner = StaticPlanner(model=model)

        if isinstance(binding_engine, str):
            self.binding_engine = get_binding_engine(binding_engine)
        else:
            self.binding_engine = binding_engine

        self.task_schemas_store: dict[str, Any] = {}

    async def run_plan(self, plan: UnifiedPlan | StaticPlan) -> ExecutionContext:
        if not isinstance(plan, UnifiedPlan):
            plan = UnifiedPlan.model_validate(plan.model_dump())
        ctx = ExecutionContext()
        logger.info(f"Starting execution of static plan containing {len(plan.tasks)} tasks.")

        # Resolve mismatched task reference names dynamically
        actual_ids = [t.id for t in plan.tasks]
        id_map = {}
        for idx, task in enumerate(plan.tasks):
            if task.args:
                refs = _extract_task_references(task.args)
                for ref in refs:
                    ref_name = ref.lstrip("$")
                    if ref_name not in actual_ids:
                        candidates = [aid for aid in actual_ids[:idx] if aid in ref_name or ref_name in aid]
                        if not candidates and idx == 1:
                            candidates = [plan.tasks[0].id]
                        if candidates:
                            id_map[ref_name] = candidates[0]
        if id_map:
            logger.info(f"Fuzzy matching mismatched task references: {id_map}")
            for task in plan.tasks:
                if task.args:
                    task.args = _rename_task_references(task.args, id_map)

        tools_list = await self.session.list_tools()
        tools_map = {t.name: t for t in tools_list}

        for task in plan.tasks:
            logger.info(f"Executing task '{task.id}' using tool '{task.tool_name}'...")
            target_tool_metadata = tools_map.get(task.tool_name)
            target_tool_input_schema = target_tool_metadata.input_schema if target_tool_metadata else {}

            resolved_args = self._resolve_variables(
                task.args,
                ctx.store,
                target_tool_input_schema=target_tool_input_schema,
            )

            # Ensure there are no unresolved references or tokens left
            def find_unresolved_issue(v: Any) -> str | None:
                if v == self.binding_failed_token:
                    return f"Sent by Planner due to missing input data ('{self.binding_failed_token}')"
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

            # Auto-wrap in {"input": ...} if required
            if (
                target_tool_input_schema
                and "input" in target_tool_input_schema.get("properties", {})
                and isinstance(resolved_args, dict)
                and "input" not in resolved_args
            ):
                resolved_args = {"input": resolved_args}

            logger.debug(f"Resolved call arguments for tool '{task.tool_name}': {resolved_args}")

            result = await self.session.call_tool(name=task.tool_name, arguments=resolved_args)

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
                "output_schema": target_tool_metadata.output_schema if target_tool_metadata else {},
            }

        logger.info("Execution of static plan completed successfully.")
        return ctx

    def _resolve_variables(
        self,
        args: Any,
        store: dict[str, Any],
        target_tool_input_schema: dict[str, Any] | None = None,
        task_schemas_store: dict[str, Any] | None = None,
    ) -> Any:
        context = BindingContext.from_dict(store)
        if task_schemas_store:
            context.metadata.update(task_schemas_store)
        else:
            context.metadata.update(self.task_schemas_store)

        return resolve_variables(
            payload=args,
            context=context,
            engine=self.binding_engine,
            target_schema=target_tool_input_schema,
        )


class DynamicExecutor:
    def __init__(
        self,
        session: MCPSessionProtocol,
        model: Any | None = None,
        model_name: str = "gemini-2.5-flash",
        prompt: PromptComposer | None = None,
        dynamic_binding_mode: DynamicBindingMode | None = DynamicBindingMode.JMESPATH_VALIDATE,
    ) -> None:
        self.session = session
        self.dynamic_binding_mode = dynamic_binding_mode or DynamicBindingMode.JMESPATH_VALIDATE
        self.binding_failed_token = DEFAULT_BINDING_FAILED_TOKEN
        self.prompt = prompt

        from src.agent.planner import DynamicPlanner

        self.planner = DynamicPlanner(model=model, model_name=model_name, prompt=prompt)

        # Default LLM runner for binder using injected model/model_name
        from src.shared.llm_client import run_structured_llm

        def default_llm_runner(variables: dict[str, Any], schema: Any) -> Any:
            prompt_composer = prompt or PromptComposer.from_file(
                "bind_prompt_dynamic.yaml", PROMPTS_DIR, template_format="yaml"
            )
            prompt_composer.set_variables(variables)
            prompt_text = prompt_composer.render()
            return run_structured_llm(
                prompt_text=prompt_text,
                prompt_variables={},
                schema=schema,
                model_name=model_name,
                base_model=model,
            )

        self.binder = DynamicDataBinder(llm_runner=default_llm_runner)
        self.task_schemas_store: dict[str, Any] = {}

    async def run_plan(self, plan: UnifiedPlan | DynamicPlan) -> ExecutionContext:
        if not isinstance(plan, UnifiedPlan):
            plan = UnifiedPlan.model_validate(plan.model_dump())
        ctx = ExecutionContext()
        logger.info(f"Starting execution of dynamic plan containing {len(plan.tasks)} tasks.")

        tools_list = await self.session.list_tools()
        tools_map = {t.name: t for t in tools_list}

        for task in plan.tasks:
            logger.info(f"Executing task '{task.id}' using tool '{task.tool_name}'...")
            target_tool_metadata = tools_map.get(task.tool_name)
            target_tool_input_schema = target_tool_metadata.input_schema if target_tool_metadata else {}

            mode = self.dynamic_binding_mode

            dependency_context = {dep_id: ctx.store[dep_id] for dep_id in task.depends_on if dep_id in ctx.store}

            if mode == DynamicBindingMode.LLM_DIRECT:
                # LLM DIRECT BINDING
                resolved_args = self._llm_direct_bind(
                    tool_name=task.tool_name,
                    input_schema=target_tool_input_schema,
                    input_description=task.input_description or task.reason or "",
                    dependency_context=dependency_context,
                )
            else:
                # Construct expected source schema at planning time
                expected_source_schema = None
                if task.depends_on and task.args_jmespath:
                    expected_schemas = {}
                    for dep_id in task.depends_on:
                        if dep_id in self.task_schemas_store:
                            expected_schemas[dep_id] = self.task_schemas_store[dep_id]["output_schema"]
                    if len(expected_schemas) == 1:
                        expected_source_schema = next(iter(expected_schemas.values()))
                    elif len(expected_schemas) > 1:
                        expected_source_schema = {
                            "type": "object",
                            "properties": expected_schemas,
                            "required": list(expected_schemas.keys()),
                        }

                # Determine planned path based on mode
                planned_path = task.args_jmespath if mode == DynamicBindingMode.JMESPATH_VALIDATE else None

                resolved_args = self._llm_bind(
                    tool_name=task.tool_name,
                    input_schema=target_tool_input_schema,
                    input_description=task.input_description or task.reason or "",
                    dependency_context=dependency_context,
                    planned_jmespath=planned_path,
                    expected_source_schema=expected_source_schema,
                )

            # Auto-wrap in {"input": ...} if required
            if (
                target_tool_input_schema
                and "input" in target_tool_input_schema.get("properties", {})
                and isinstance(resolved_args, dict)
                and "input" not in resolved_args
            ):
                resolved_args = {"input": resolved_args}

            logger.debug(f"Resolved call arguments for tool '{task.tool_name}': {resolved_args}")

            result = await self.session.call_tool(name=task.tool_name, arguments=resolved_args)

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
                "output_schema": target_tool_metadata.output_schema if target_tool_metadata else {},
            }

        logger.info("Execution of dynamic plan completed successfully.")
        return ctx

    def _llm_bind(
        self,
        tool_name: str,  # noqa: ARG002
        input_schema: dict[str, Any],
        input_description: str,
        dependency_context: dict[str, Any],
        planned_jmespath: str | None = None,
        expected_source_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Wrapper for LLM dynamic binding."""
        return self.binder.bind_with_validation(
            intent=input_description,
            source_data=dependency_context,
            target_schema=input_schema,
            planned_path=planned_jmespath,
            expected_source_schema=expected_source_schema,
        )

    def _llm_direct_bind(
        self,
        tool_name: str,  # noqa: ARG002
        input_schema: dict[str, Any],
        input_description: str,
        dependency_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Wrapper for direct LLM binding."""
        return self.binder.bind_directly(
            intent=input_description,
            source_data=dependency_context,
            target_schema=input_schema,
            model=getattr(self.planner, "model", None),
            model_name=getattr(self.planner, "model_name", "gemini-2.5-flash"),
        )


# Backward compatibility aliases
UnifiedExecutor = DynamicExecutor
