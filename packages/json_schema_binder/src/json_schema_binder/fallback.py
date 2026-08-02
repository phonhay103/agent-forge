import json
from typing import Any, Dict, Optional, Union, Type
from pydantic import BaseModel

DEFAULT_FALLBACK_PROMPT = """You are a Schema-Conforming Data Mapper.
Your task is to resolve and map unresolved variable references (such as '$step_1...') in the input payload using the provided source context data.

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
    Independent Runtime Fallback Engine using LangChain Structured Output.
    Repairs or resolves payloads and arguments when deterministic binding fails.
    
    Fully decoupled: Accepts any general LangChain ChatModel instance 
    (ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI, ChatOllama, etc.) 
    and an optional custom prompt template.
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
        context_store: Dict[str, Any],
        target_schema: Union[Dict[str, Any], Type[BaseModel], Any],
        partially_resolved_payload: Any,
        directive: Optional[str] = None,
        llm: Optional[Any] = None,
        custom_prompt_template: Optional[str] = None,
    ) -> Any:
        """
        Generic method to resolve and repair a payload to match a target schema.
        Oblivious of agent-specific logic, terms, or environments.
        """
        if not target_schema:
            raise ValueError("target_schema is required for structured LLM fallback.")

        active_llm = llm or self._llm
        if active_llm is None:
            raise ValueError(
                "LLMFallbackMapper requires a valid LLM model instance "
                "(e.g., ChatOpenAI, ChatGoogleGenerativeAI, ChatAnthropic) "
                "supporting .with_structured_output()."
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

        formatted_context = json.dumps(context_store, default=str, indent=2)
        formatted_args = json.dumps(partially_resolved_payload, default=str, indent=2)

        if not hasattr(active_llm, "with_structured_output"):
            raise TypeError(
                f"Provided LLM model '{type(active_llm).__name__}' does not support .with_structured_output(). "
                "Please pass a standard LangChain ChatModel instance."
            )

        from langchain_core.prompts import ChatPromptTemplate

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

        if isinstance(result, BaseModel):
            return result.model_dump()
        return result
