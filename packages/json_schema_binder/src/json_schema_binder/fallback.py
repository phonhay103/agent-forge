import json
import logging
from typing import Any, Dict, Optional, Union, Type, Callable
from pydantic import BaseModel

from json_schema_binder.models import BindingContext
from json_schema_binder.parser import VariableParser

logger = logging.getLogger("json_schema_binder.fallback")

DEFAULT_FALLBACK_PROMPT = """You are a Schema-Conforming Data Mapper.
Your task is to resolve and map unresolved variable references in the input payload using the provided source context data.

Target Schema:
{target_schema}

Directive / Mapping Instructions:
{directive}

Source Context Data:
{context_data}

Partially Resolved Payload:
{partially_resolved_payload}

Analyze the source context data and resolve/repair the payload to strictly conform to the target schema.
"""


class LLMFallbackMapper:
    """
    Independent Runtime Fallback Engine using LangChain Structured Output or Generic LLM Callable.
    Repairs or resolves payloads and arguments when deterministic binding fails.
    """
    def __init__(
        self,
        model: Optional[Any] = None,
        prompt_template: Optional[str] = None
    ):
        self._llm = model
        self.prompt_template = prompt_template or DEFAULT_FALLBACK_PROMPT

    def repair_payload(
        self,
        context_store: Union[BindingContext, Dict[str, Any], Any],
        target_schema: Union[Dict[str, Any], Type[BaseModel], Any],
        partially_resolved_payload: Any,
        directive: Optional[str] = None,
        llm: Optional[Any] = None,
        custom_prompt_template: Optional[str] = None,
    ) -> Any:
        """
        Generic method to resolve and repair a payload to match a target schema.
        Accepts BindingContext or raw dict context store.
        """
        unresolved = VariableParser.extract_unresolved_references(partially_resolved_payload)
        logger.warning(
            f"⚠️ [LLM FALLBACK TRIGGERED] Deterministic binding failed for unresolved references: {unresolved}. "
            f"Invoking LLM Fallback Mapper (Directive: '{directive or 'N/A'}')..."
        )

        if not target_schema:
            raise ValueError("target_schema is required for structured LLM fallback.")

        if isinstance(context_store, BindingContext):
            context_data = context_store.data
        elif isinstance(context_store, dict):
            context_data = context_store
        else:
            context_data = getattr(context_store, "data", context_store)

        active_llm = llm or self._llm
        if active_llm is None:
            raise ValueError(
                "LLMFallbackMapper requires a valid LLM model instance or callable "
                "(e.g., ChatOpenAI, ChatGoogleGenerativeAI, ChatAnthropic) "
                "supporting structured output."
            )

        # Handle Pydantic model vs Dict schema
        if isinstance(target_schema, type) and issubclass(target_schema, BaseModel):
            schema_for_structured = target_schema
            schema_dict = target_schema.model_json_schema()
            target_schema_name = target_schema.__name__
        elif hasattr(target_schema, "model_dump"):
            schema_for_structured = target_schema.__class__
            schema_dict = target_schema.model_json_schema()
            target_schema_name = target_schema.__class__.__name__
        elif isinstance(target_schema, dict):
            safe_schema = dict(target_schema)
            if "type" not in safe_schema:
                safe_schema["type"] = "object"
            schema_for_structured = safe_schema
            schema_dict = safe_schema
            target_schema_name = safe_schema.get("title", "TargetSchema")
        else:
            schema_for_structured = target_schema
            schema_dict = {"type": "object"}
            target_schema_name = "TargetSchema"

        formatted_context = json.dumps(context_data, default=str, indent=2)
        formatted_args = json.dumps(partially_resolved_payload, default=str, indent=2)

        # If custom callable is provided
        if callable(active_llm) and not hasattr(active_llm, "with_structured_output"):
            raw_prompt = custom_prompt_template or self.prompt_template
            prompt_str = raw_prompt.format(
                context_data=formatted_context,
                target_schema_name=target_schema_name,
                target_schema=json.dumps(schema_dict, indent=2),
                partially_resolved_payload=formatted_args,
                directive=directive or "N/A"
            )
            return active_llm(prompt_str, schema_for_structured)

        if not hasattr(active_llm, "with_structured_output"):
            raise TypeError(
                f"Provided LLM model '{type(active_llm).__name__}' does not support .with_structured_output(). "
                "Please pass a standard LangChain ChatModel instance or structured LLM callable."
            )

        try:
            from langchain_core.prompts import ChatPromptTemplate
        except ImportError as e:
            raise ImportError(
                "langchain-core is required for LLMFallbackMapper with LangChain models. "
                "Please install via: pip install 'json-schema-binder[llm]'"
            ) from e

        raw_prompt = custom_prompt_template or self.prompt_template
        prompt_template_obj = ChatPromptTemplate.from_template(raw_prompt)
        structured_llm = active_llm.with_structured_output(schema_for_structured)
        chain = prompt_template_obj | structured_llm

        result = chain.invoke({
            "context_data": formatted_context,
            "target_schema_name": target_schema_name,
            "target_schema": json.dumps(schema_dict, indent=2),
            "partially_resolved_payload": formatted_args,
            "directive": directive or "N/A"
        })

        out = result.model_dump() if isinstance(result, BaseModel) else result
        logger.info(f"✅ [LLM FALLBACK REPAIRED] Payload successfully repaired by LLM: {out}")
        return out

