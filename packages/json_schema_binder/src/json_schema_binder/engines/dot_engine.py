from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine
from json_schema_binder.models import (
    BindingContext,
    EvaluationResult,
    MappingResult,
    MappingSpec,
)

T = TypeVar("T")


@register_binding_engine("dot_notation")
@register_binding_engine("dot")
@register_binding_engine("standard")
class DotNotationBindingEngine(BaseBindingEngine):
    @property
    def binding_type(self) -> BindingType:
        return BindingType.DOT_NOTATION

    def _traverse_path(self, curr: Any, keys: list) -> Any | None:
        for key in keys:
            if not key:
                continue
            if isinstance(curr, BaseModel):
                curr = curr.model_dump()
            if isinstance(curr, dict) and key in curr:
                curr = curr[key]
            elif isinstance(curr, list) and key.isdigit():
                idx = int(key)
                if 0 <= idx < len(curr):
                    curr = curr[idx]
                else:
                    return None
            else:
                return None
        return curr

    def evaluate(self, expression: str, source_data: Any) -> EvaluationResult[Any]:
        data = BindingContext.from_dict(source_data).data if isinstance(source_data, (dict, BindingContext, Mapping)) else source_data
        if hasattr(source_data, "model_dump") and not isinstance(source_data, (dict, BindingContext)):
            data = source_data.model_dump()


        expr = expression.strip()
        if expr.startswith("$"):
            expr = expr[1:].strip()

        if not expr:
            return EvaluationResult(
                value=data,
                expression=expression,
                is_success=True,
                engine=self.binding_type.value,
            )

        keys = expr.split(".")
        res = self._traverse_path(data, keys)
        return EvaluationResult(
            value=res,
            expression=expression,
            is_success=res is not None,
            engine=self.binding_type.value,
        )

    def transform(
        self,
        source_data: Any,
        mapping_spec: dict[str, str] | MappingSpec,
        target_schema: dict[str, Any] | type[BaseModel] | None = None,
    ) -> MappingResult[Any]:
        spec = mapping_spec.field_mappings if isinstance(mapping_spec, MappingSpec) else mapping_spec
        output: dict[str, Any] = {}
        unresolved: list = []
        errors: list = []

        for target_field, expr in spec.items():
            res = self.evaluate(expr, source_data)
            if res.is_success and res.value is not None:
                output[target_field] = res.value
            else:
                unresolved.append(expr)

        if target_schema and isinstance(target_schema, type) and issubclass(target_schema, BaseModel):
            try:
                validated_output = target_schema.model_validate(output)
                return MappingResult(
                    output=validated_output,
                    is_success=len(unresolved) == 0,
                    engine=self.binding_type.value,
                    unresolved_expressions=unresolved,
                    errors=errors,
                )
            except Exception as e:
                errors.append(f"Target schema validation error: {e}")

        return MappingResult(
            output=output,
            is_success=len(unresolved) == 0,
            engine=self.binding_type.value,
            unresolved_expressions=unresolved,
            errors=errors,
        )

    def get_system_prompt_instruction(self) -> str:
        return (
            "Variable Binding Engine: Dot Notation\n"
            "To reference values from the source context data, use standard dot notation only "
            "(e.g., \"$step_1.field_name\", \"$step_1.items.0\").\n"
            "CRITICAL REQUIREMENT FOR DOT NOTATION:\n"
            "- Do NOT use bracket filters, query expressions, or wildcards like '[?(@.price > 800)]' or '[*]'.\n"
            "- Variable bindings MUST be simple dot-separated paths containing only letters, numbers, underscores, and zero-based numeric array indices (e.g. '$step_1.items' or '$step_1.items.0.price')."
        )

    def get_regex_pattern(self) -> str:
        return r"^(\$?[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*)$"


