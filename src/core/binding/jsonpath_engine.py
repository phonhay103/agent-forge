import re

import functools
from typing import Any, Dict, Optional
from jsonpath_ng.ext import parse
from pydantic import BaseModel
from src.core.binding.base import BaseBindingEngine, BindingType, register_binding_engine



@functools.lru_cache(maxsize=1024)
def _get_compiled_jsonpath(expr: str):
    return parse(expr)


@register_binding_engine("jsonpath")
@register_binding_engine("json_path")


class JSONPathBindingEngine(BaseBindingEngine):
    @property
    def binding_type(self) -> BindingType:
        return BindingType.JSONPATH

    def resolve(
        self,
        val: Any,
        context_store: Dict[str, Any],
        target_tool_input_schema: Optional[Dict[str, Any]] = None,
        step_schemas_store: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Any:
        if isinstance(val, str) and val.startswith("$"):
            raw_ref = val[1:]
            if not raw_ref:
                return val

            match = re.match(r"^([a-zA-Z0-9_]+)(.*)$", raw_ref)
            if not match:
                return val

            step_id, rem_expr = match.groups()
            if step_id not in context_store:
                return val

            data = context_store[step_id]
            if isinstance(data, BaseModel):
                data = data.model_dump()

            if not rem_expr:
                return data

            expr = rem_expr.strip()
            if not expr.startswith("$"):
                if expr.startswith("."):
                    expr = "$" + expr
                else:
                    expr = "$." + expr

            try:
                jsonpath_expr = _get_compiled_jsonpath(expr)
                matches = [m.value for m in jsonpath_expr.find(data)]
                if not matches:
                    return val
                if len(matches) == 1 and not ("[*]" in expr or "[?" in expr or ".." in expr or ".*" in expr):
                    return matches[0]
                return matches
            except Exception:
                return val

        elif isinstance(val, BaseModel):
            return self.resolve(val.model_dump(), context_store, target_tool_input_schema, step_schemas_store)
        elif isinstance(val, dict):
            return {k: self.resolve(v, context_store, target_tool_input_schema, step_schemas_store) for k, v in val.items()}
        elif isinstance(val, list):
            return [self.resolve(v, context_store, target_tool_input_schema, step_schemas_store) for v in val]
        return val

    def get_system_prompt_instruction(self) -> str:
        return (
            "Variable Binding Engine: JSONPath\n"
            "To reference and transform outputs from previous steps in tool arguments, write JSONPath expressions "
            "directly after $step_id (e.g. \"$step_1.products[?(@.price > 500)].name\", \"$step_1.regions[*].warehouse_matrix.*\", "
            "\"$step_1.items[0]\"). "
            "The engine will automatically evaluate and resolve these expressions using JSONPath syntax before step execution."
        )
