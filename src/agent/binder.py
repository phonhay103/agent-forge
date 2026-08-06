import json
import logging
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field, model_validator

from json_schema_binder import get_binding_engine
from json_schema_binder.engines.jmespath_engine import normalize_jmespath


class BindingEngineProtocol(Protocol):
    def evaluate(self, expression: str, source_data: Any) -> Any:
        """Evaluates a single expression against source data."""
        ...

logger = logging.getLogger("data_binder")

class DataMappingPath(BaseModel):
    """Pydantic model representing structured LLM output for mapping path expressions."""
    path_expression: str = Field(
        default="",
        description="A single, valid JMESPath expression that compiles and transforms the source context data into an object matching the target schema."
    )
    jmespath_expression: str | None = Field(
        default=None,
        description="Deprecated/backward-compatible field name."
    )

    @model_validator(mode="before")
    @classmethod
    def populate_expressions(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "jmespath_expression" in data and not data.get("path_expression"):
                data["path_expression"] = data["jmespath_expression"]
            if "path_expression" in data and not data.get("jmespath_expression"):
                data["jmespath_expression"] = data["path_expression"]
        return data


def generate_schema(val: Any) -> dict[str, Any]:
    """Recursively generates a standard JSON Schema from a Python object."""
    if isinstance(val, dict):
        properties = {}
        required = []
        for k, v in val.items():
            properties[k] = generate_schema(v)
            required.append(k)
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema
    elif isinstance(val, list):
        if len(val) > 0:
            items_schema = generate_schema(val[0])
        else:
            items_schema = {}
        return {"type": "array", "items": items_schema}
    elif isinstance(val, bool):
        return {"type": "boolean"}
    elif isinstance(val, int):
        return {"type": "integer"}
    elif isinstance(val, float):
        return {"type": "number"}
    elif isinstance(val, str):
        return {"type": "string"}
    elif val is None:
        return {"type": "null"}
    else:
        return {"type": "string"}


def schemas_match(expected: Any, actual: Any) -> bool:
    """Recursively compares structural aspects of two JSON schemas (types, properties, items)."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return expected == actual

    # Compare 'type'
    if expected.get("type") != actual.get("type"):
        return False

    # Compare 'properties' recursively
    expected_props = expected.get("properties", {})
    actual_props = actual.get("properties", {})
    if set(expected_props.keys()) != set(actual_props.keys()):
        return False
    for key in expected_props:
        if not schemas_match(expected_props[key], actual_props[key]):
            return False

    # Compare 'items' recursively
    if "items" in expected or "items" in actual:
        if not schemas_match(expected.get("items"), actual.get("items")):
            return False

    return True


class DynamicDataBinder:
    """
    Decoupled layer for dynamic binding using schema generation and path transformation.
    Adheres to dependency injection by accepting an LLM runner callable.
    """
    def __init__(
        self,
        llm_runner: Callable[[dict[str, Any], Any], Any],
        binding_engine: BindingEngineProtocol | None = None,
    ):
        """
        Args:
            llm_runner: Callable that accepts a dict of prompt variables and response schema,
                        and returns the parsed structured output.
            binding_engine: Optional conformant binding engine for evaluation.
        """
        self.llm_runner = llm_runner
        self.binding_engine = binding_engine or get_binding_engine("jmespath")

    def bind_dynamically(
        self,
        intent: str,
        source_data: dict[str, Any],
        target_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """
        1. Auto-generates JSON Schema for actual source_data.
        2. Uses LLM runner to map source schema to target schema and output a JMESPath mapping path.
        3. Executes the mapping path expression on source_data to resolve final arguments.
        """
        source_schema = generate_schema(source_data)
        logger.info(f"Generated source schema for context: {json.dumps(source_schema)}")

        variables = {
            "intent": intent,
            "source_schema": json.dumps(source_schema, indent=2),
            "target_schema": json.dumps(target_schema, indent=2),
        }

        logger.info(f"Invoking LLM to generate mapping path for intent: '{intent}'")
        result = self.llm_runner(variables, DataMappingPath)

        if isinstance(result, BaseModel):
            path_expr = getattr(result, "path_expression", "")
        elif isinstance(result, dict):
            path_expr = result.get("path_expression", "")
        else:
            path_expr = str(result)

        path_expr = path_expr.strip()

        # Clean any accidental markdown codeblock wrappers
        if path_expr.startswith("```"):
            lines = path_expr.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1] == "```":
                lines = lines[:-1]
            path_expr = "\n".join(lines).strip()

        path_expr = normalize_jmespath(path_expr)
        logger.info(f"Generated path expression: {path_expr}")

        try:
            res = self.binding_engine.evaluate(path_expr, source_data)
            if hasattr(res, "is_success"):
                if not res.is_success:
                    raise ValueError(res.error or "Evaluation failed")
                resolved_args = res.value
            else:
                resolved_args = res
        except Exception as e:
            logger.error(f"Failed to execute path expression '{path_expr}' on source data: {e}")
            raise ValueError(f"Mapping path execution failed: {e}") from e

        if not isinstance(resolved_args, dict):
            if resolved_args is None:
                resolved_args = {}
            else:
                logger.warning(f"Mapping path output is not a dictionary: {resolved_args}")

        return resolved_args

    def bind(
        self,
        intent: str,
        source_data: dict[str, Any],
        target_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Legacy compatibility wrapper for bind_dynamically."""
        return self.bind_dynamically(
            intent=intent,
            source_data=source_data,
            target_schema=target_schema,
        )

    def bind_with_validation(
        self,
        intent: str,
        source_data: dict[str, Any],
        target_schema: dict[str, Any],
        planned_path: str | None = None,
        expected_source_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Attempts to use planned_path if expected_source_schema matches the runtime actual schema.
        Otherwise triggers dynamic path generation via LLM.
        """
        actual_schema = generate_schema(source_data)

        if planned_path and expected_source_schema:
            planned_path = normalize_jmespath(planned_path)
            if schemas_match(expected_source_schema, actual_schema):
                logger.info(f"Reusing pre-planned path: '{planned_path}' (schemas match)")
                try:
                    res = self.binding_engine.evaluate(planned_path, source_data)
                    if hasattr(res, "is_success"):
                        if not res.is_success:
                            raise ValueError(res.error or "Evaluation failed")
                        resolved_args = res.value
                    else:
                        resolved_args = res

                    if isinstance(resolved_args, dict):
                        return resolved_args
                    elif resolved_args is None:
                        return {}
                    else:
                        logger.warning(f"Pre-planned path output is not a dictionary: {resolved_args}")
                except Exception as e:
                    logger.warning(f"Pre-planned path evaluation failed: {e}. Re-binding dynamically.")
            else:
                logger.info("Runtime schema does not match planning-time schema. Re-binding dynamically.")
        else:
            logger.info("No pre-planned path expression or expected schema available. Binding dynamically.")

        return self.bind_dynamically(intent, source_data, target_schema)

    def bind_with_fallback(
        self,
        intent: str,
        source_data: dict[str, Any],
        target_schema: dict[str, Any],
        planned_jmespath: str | None = None,
        expected_source_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Legacy compatibility wrapper mapping to bind_with_validation."""
        return self.bind_with_validation(
            intent=intent,
            source_data=source_data,
            target_schema=target_schema,
            planned_path=planned_jmespath,
            expected_source_schema=expected_source_schema,
        )

    def bind_directly(
        self,
        intent: str,
        source_data: dict[str, Any],
        target_schema: dict[str, Any],
        model: Any | None = None,
        model_name: str = "gemini-2.5-flash",
    ) -> dict[str, Any]:
        """Use LLM directly to resolve tool arguments fitting the target schema without JMESPath."""
        from prompt_composer import PromptComposer
        from src.shared.llm_client import run_structured_llm

        prompt = PromptComposer(
            template="""You are a Schema-Conforming Data Mapper.
Your task is to map values from the Source Context Data to produce a target JSON object that strictly conforms to the Target Schema based on the User Intent.

User Intent:
{intent}

Target Schema:
{target_schema}

Source Context Data:
{context_data}

Analyze the source context data and generate the output JSON conforming to the Target Schema.
"""
        )
        prompt.set_variables({
            "intent": intent,
            "target_schema": json.dumps(target_schema, indent=2),
            "context_data": json.dumps(source_data, indent=2),
        })
        prompt_text = prompt.render()

        res = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={},
            schema=target_schema,
            model_name=model_name,
            base_model=model,
        )
        if isinstance(res, dict):
            return res
        elif hasattr(res, "model_dump"):
            return res.model_dump()
        return {}


# Backward compatibility aliases
DynamicJMESPathBinder = DynamicDataBinder
JMESPathMapping = DataMappingPath
