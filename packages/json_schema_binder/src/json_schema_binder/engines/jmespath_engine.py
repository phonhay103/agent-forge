import functools
from typing import Any, Dict, Optional, TypeVar, Union, Type, Mapping

import jmespath
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
def _get_compiled_jmespath(expr: str):
    return jmespath.compile(expr)


@register_binding_engine("jmespath")
@register_binding_engine("jmes")
class JMESPathBindingEngine(BaseBindingEngine):
    @property
    def binding_type(self) -> BindingType:
        return BindingType.JMESPATH

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

        try:
            compiled = _get_compiled_jmespath(expr)
            res = compiled.search(data)
            return EvaluationResult(
                value=res,
                expression=expression,
                is_success=res is not None,
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
        mapping_spec: Union[Dict[str, str], MappingSpec],
        target_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
    ) -> MappingResult[Any]:
        spec = mapping_spec.field_mappings if isinstance(mapping_spec, MappingSpec) else mapping_spec
        output: Dict[str, Any] = {}
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
            "Variable Binding Engine: JMESPath\n"
            "To reference and transform values from the source context data, write direct JMESPath expressions "
            "(e.g., \"items[?price > `500`].name\", \"regions[*].warehouse_matrix[][]\", "
            "\"division_summaries | max_by(@, &total_budget)\", \"skus[0]\")."
        )


