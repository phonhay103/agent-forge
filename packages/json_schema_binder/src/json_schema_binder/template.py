import re
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine
from json_schema_binder.factory import get_binding_engine
from json_schema_binder.models import BindingContext

T = TypeVar("T")


class TemplateResolver:
    """
    Decoupled utility for parsing template payloads containing variable expressions (e.g. '$user.name')
    and delegating evaluation directly to a binding engine's evaluate() method.
    """
    def __init__(self, engine: str | BaseBindingEngine = "jmespath") -> None:
        self.engine = get_binding_engine(engine) if isinstance(engine, str) else engine

    def resolve_payload(self, payload: T, source_data: Any) -> T:
        if isinstance(source_data, BindingContext):
            data = source_data.data
        elif hasattr(source_data, "model_dump"):
            data = source_data.model_dump()
        else:
            data = source_data

        if isinstance(payload, str) and payload.startswith("$"):
            expr = payload[1:].strip()
            if not expr:
                return payload

            # Try direct expression evaluation
            eval_res = self.engine.evaluate(expr, data)
            if eval_res.is_success and eval_res.value is not None:
                return eval_res.value

            # If expression starts with a var_key prefix (e.g. "step_1.result") and var_key in data
            match = re.match(r"^([a-zA-Z0-9_]+)(.*)$", expr)
            if match:
                var_key, rem_expr = match.groups()
                if isinstance(data, dict) and var_key in data:
                    sub_data = data[var_key]
                    rem_expr = rem_expr.strip()
                    if rem_expr.startswith("."):
                        rem_expr = rem_expr[1:].strip()

                    if not rem_expr:
                        return sub_data

                    sub_res = self.engine.evaluate(rem_expr, sub_data)
                    if sub_res.is_success and sub_res.value is not None:
                        return sub_res.value

            return payload

        elif isinstance(payload, BaseModel):
            resolved_dict = self.resolve_payload(payload.model_dump(), data)
            try:
                return payload.__class__.model_validate(resolved_dict)
            except Exception:
                return resolved_dict
        elif isinstance(payload, dict):
            return cast(T, {k: self.resolve_payload(v, data) for k, v in payload.items()})
        elif isinstance(payload, list):
            return cast(T, [self.resolve_payload(v, data) for v in payload])
        return payload
