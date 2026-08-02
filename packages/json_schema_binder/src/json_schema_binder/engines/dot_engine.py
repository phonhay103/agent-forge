from typing import Any, Dict, Optional

from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine


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
        target_schema: Optional[Dict[str, Any]] = None,
        metadata_store: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        if isinstance(val, str) and val.startswith("$"):
            raw_ref = val[1:]
            if not raw_ref:
                return val

            path = raw_ref.split(".")
            var_key = path[0]
            if var_key not in context_store:
                return val

            curr = context_store[var_key]
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
            return self.resolve(val.model_dump(), context_store, target_schema, metadata_store, **kwargs)
        elif isinstance(val, dict):
            return {k: self.resolve(v, context_store, target_schema, metadata_store, **kwargs) for k, v in val.items()}
        elif isinstance(val, list):
            return [self.resolve(v, context_store, target_schema, metadata_store, **kwargs) for v in val]
        return val

    def get_system_prompt_instruction(self) -> str:
        return (
            "Variable Binding Engine: Dot Notation\n"
            "To reference values from the source context data in the payload, use standard dot notation "
            "after the variable name starting with $ (e.g., \"$var_name.field_name\", \"$var_name.items.0\"). "
            "The engine will automatically extract the specified key or list index before final execution."
        )
