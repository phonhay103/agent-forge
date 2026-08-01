from typing import Any, Dict, Optional
from pydantic import BaseModel
from src.core.binding.base import BaseBindingEngine, BindingType, register_binding_engine


@register_binding_engine("dot_notation")
@register_binding_engine("dot")
@register_binding_engine("standard")
class DotNotationBindingEngine(BaseBindingEngine):
    @property
    def binding_type(self) -> BindingType:
        return BindingType.DOT_NOTATION

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

            path = raw_ref.split(".")
            step_id = path[0]
            if step_id not in context_store:
                return val

            curr = context_store[step_id]
            if isinstance(curr, BaseModel):
                curr = curr.model_dump()

            for key in path[1:]:
                if isinstance(curr, dict) and key in curr:
                    curr = curr[key]
                elif isinstance(curr, list) and key.isdigit():
                    curr = curr[int(key)]
                else:
                    return val
            return curr

        elif isinstance(val, BaseModel):
            return self.resolve(val.model_dump(), context_store, target_tool_input_schema, step_schemas_store)
        elif isinstance(val, dict):
            return {k: self.resolve(v, context_store, target_tool_input_schema, step_schemas_store) for k, v in val.items()}
        elif isinstance(val, list):
            return [self.resolve(v, context_store, target_tool_input_schema, step_schemas_store) for v in val]
        return val

    def get_system_prompt_instruction(self) -> str:
        return (
            "Variable Binding Engine: Dot Notation\n"
            "To reference outputs from previous steps in tool arguments, use standard dot notation "
            "after $step_id (e.g. \"$step_1.field_name\", \"$step_1.items.0\"). "
            "The engine will automatically extract the specified key or list index before step execution."
        )
