import functools
from collections.abc import Mapping
from typing import Any, TypeVar

from jsonpath_ng.ext import parse
from pydantic import BaseModel

from json_schema_binder.base import BaseBindingEngine, BindingType, register_binding_engine
from json_schema_binder.models import (
    BindingContext,
    EvaluationResult,
    MappingResult,
    MappingSpec,
)

T = TypeVar("T")


@functools.lru_cache(maxsize=1024)
def _get_compiled_jsonpath(expr: str):
    return parse(expr)


@register_binding_engine("jsonpath")
@register_binding_engine("json_path")
class JSONPathBindingEngine(BaseBindingEngine):
    @property
    def binding_type(self) -> BindingType:
        return BindingType.JSONPATH

    def evaluate(self, expression: str, source_data: Any) -> EvaluationResult[Any]:
        data = BindingContext.from_dict(source_data).data if isinstance(source_data, (dict, BindingContext, Mapping)) else source_data
        if hasattr(source_data, "model_dump") and not isinstance(source_data, (dict, BindingContext)):
            data = source_data.model_dump()


        expr = expression.strip()
        if not expr.startswith("$"):
            if expr.startswith("."):
                expr = "$" + expr
            else:
                expr = "$." + expr

        try:
            jsonpath_expr = _get_compiled_jsonpath(expr)
            matches = [m.value for m in jsonpath_expr.find(data)]
            if not matches:
                return EvaluationResult(
                    value=None,
                    expression=expression,
                    is_success=False,
                    engine=self.binding_type.value,
                )
            if len(matches) == 1 and not any(op in expr for op in ("[*]", "[?", "..", ".*")):
                res_val = matches[0]
            else:
                res_val = matches
            return EvaluationResult(
                value=res_val,
                expression=expression,
                is_success=True,
                engine=self.binding_type.value,
            )
        except Exception as e:
            return EvaluationResult(
                value=None,
                expression=expression,
                is_success=False,
                engine=self.binding_type.value,
                error=str(e),
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
                if res.error:
                    errors.append(f"{target_field}: {res.error}")

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
            "Variable Binding Engine: JSONPath\n"
            "To reference and transform values from the source context data, write direct JSONPath expressions "
            "(e.g., \"$.products[?(@.price > 500)].name\", \"$.regions[*].warehouse_matrix.*\", \"$.items[0]\")."
        )

    def get_regex_pattern(self) -> str:
        return r"^(\$?\.?[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+|\[.*?\])*)$"


