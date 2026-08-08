import functools
import re
from collections.abc import Mapping
from typing import Any, TypeVar, override

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
def _get_compiled_jmespath(expr: str) -> Any:
    return jmespath.compile(expr)


def balance_json_brackets(json_str: str) -> str:
    """
    Idempotent helper that repairs truncated/unbalanced JSON bracket sequences at the end of a string.
    """
    stripped = json_str.rstrip()
    prefix = stripped.rstrip('}]')
    open_brackets = []
    in_string = False
    escape = False

    for c in prefix:
        if escape:
            escape = False
            continue
        if c == '\\':
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue

        if c in '{[':
            open_brackets.append(c)
        elif c in '}]':
            if not open_brackets:
                continue
            if (c == '}' and open_brackets[-1] == '{') or (c == ']' and open_brackets[-1] == '['):
                open_brackets.pop()

    closing = []
    for b in reversed(open_brackets):
        if b == '{':
            closing.append('}')
        else:
            closing.append(']')

    return prefix + ''.join(closing)


def normalize_jmespath(expr: str) -> str:
    """
    Cleans up common JSON-style formatting mistakes made by LLMs in JMESPath expressions,
    such as wrapping keys in double quotes or wrapping backticked literals in double quotes.
    Safely preserves JSON literals enclosed in backticks.
    """
    if not expr:
        return expr
    expr = expr.strip()

    # If the expression starts with a backtick but does not end with one, append the closing backtick.
    if expr.startswith('`') and not expr.endswith('`'):
        expr = expr + '`'

    # If the entire expression is wrapped in backticks, it is a single top-level JSON literal.
    if expr.startswith('`') and expr.endswith('`'):
        content = expr[1:-1]
        balanced = balance_json_brackets(content)
        return '`' + balanced + '`'

    # 1. Fix double quotes wrapped around backticked literals, e.g.,
    # key: "`value`" or key: "`"value"`"
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        val = match.group(2).strip()
        val_clean = val.strip('"\'')

        if val_clean.lower() in ('true', 'false') or val_clean.replace('.', '', 1).isdigit():
            return f"{key}: `{val_clean}`"
        else:
            return f"{key}: `\"{val_clean}\"`"

    expr = re.sub(r'"?(\w+)"?:\s*"`([^`]+)`"', replacer, expr)

    # 2. Split by backticks to process keys/identifiers only outside of literals
    parts = expr.split('`')
    for i in range(len(parts)):
        if i % 2 == 0:
            # We are outside backticks; safe to strip double quotes from keys
            parts[i] = re.sub(r'"(\w+)":', r'\1:', parts[i])
        else:
            # We are inside a JSON literal; balance its brackets
            parts[i] = balance_json_brackets(parts[i])

    return '`'.join(parts)


@register_binding_engine("jmespath")
@register_binding_engine("jmes")
class JMESPathBindingEngine(BaseBindingEngine):
    @property
    @override
    def binding_type(self) -> BindingType:
        return BindingType.JMESPATH

    @override
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
            cleaned_expr = normalize_jmespath(expr)
            compiled = _get_compiled_jmespath(cleaned_expr)
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

    @override
    def transform(
        self,
        source_data: Any,
        mapping_spec: dict[str, str] | MappingSpec,
        target_schema: dict[str, Any] | type[BaseModel] | None = None,
    ) -> MappingResult[Any]:
        spec = mapping_spec.field_mappings if isinstance(mapping_spec, MappingSpec) else mapping_spec
        output: dict[str, Any] = {}
        unresolved: list[str] = []
        errors: list[str] = []

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

    @override
    def get_system_prompt_instruction(self) -> str:
        return (
            "Variable Binding Engine: JMESPath\n"
            "To reference and transform values from the source context data, write direct JMESPath expressions "
            "(e.g., \"items[?price > `500`].name\", \"regions[*].warehouse_matrix[][]\", "
            "\"division_summaries | max_by(@, &total_budget)\", \"skus[0]\")."
        )

    @override
    def get_regex_pattern(self) -> str:
        return r"^(\$?[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+|\[.*?\]|\s*\|\s*.*|\{.*?\})*)$"


