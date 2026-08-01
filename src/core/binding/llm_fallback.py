import os
import json
from typing import Any, Dict, Optional


class LLMFallbackMapper:
    """
    Automatic Runtime Fallback Engine using LangChain LCEL & LLM (gemini-3.5-flash-lite) with Structured Output.
    Repairs the entire tool argument payload simultaneously when deterministic binding fails.
    """
    def __init__(self, model: Optional[Any] = None, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self._llm = model

    def repair_arguments(
        self,
        context_store: Dict[str, Any],
        target_tool_input_schema: Dict[str, Any],
        partially_resolved_args: Any,
        directive: Optional[str] = None
    ) -> Any:
        if not hasattr(self, "_llm") or self._llm is None:
            from src.core.llm_client import get_llm_client
            self._llm = get_llm_client(model_name=self.model_name, temperature=0.0)
        llm = self._llm

        
        if not target_tool_input_schema:
            raise ValueError("target_tool_input_schema is required for structured LLM fallback.")

        target_tool_name = target_tool_input_schema.get("title", "TargetTool")
        formatted_context = json.dumps(context_store, default=str, indent=2)
        formatted_args = json.dumps(partially_resolved_args, default=str, indent=2)
        
        # Ensure the schema is a valid JSON schema object format
        safe_schema = dict(target_tool_input_schema)
        if "type" not in safe_schema:
            safe_schema["type"] = "object"

        from src.core.llm_client import run_structured_llm
        return run_structured_llm(
            prompt_name="fallback_prompt.md",
            prompt_variables={
                "context_data": formatted_context,
                "target_tool_name": target_tool_name,
                "target_schema": json.dumps(safe_schema, indent=2),
                "partially_resolved_args": formatted_args,
                "directive": directive or "N/A"
            },
            schema=safe_schema,
            base_model=llm,
            model_name=self.model_name
        )

