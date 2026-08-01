from typing import List, Any, Union, Optional
from src.core.binding import BaseBindingEngine, get_binding_engine
from pydantic import BaseModel, Field
import json

from src.core.planner.models import StepArgument, PlanStep, Plan

class Planner:
    def __init__(self, model: Optional[Any] = None, model_name: str = "gemini-2.5-flash"):
        self.model = model
        self.model_name = model_name
    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
        binding_type: Union[str, BaseBindingEngine] = "jmespath",
        enable_llm_fallback: bool = False
    ) -> Plan:
        engine = get_binding_engine(binding_type) if isinstance(binding_type, str) else binding_type
        binding_instruction = engine.get_system_prompt_instruction()

        fallback_instruction = ""
        if enable_llm_fallback:
            fallback_instruction = (
                "\nLLM FALLBACK MODE IS ENABLED.\n"
                "For steps referencing previous step outputs, generate a 'directive' field in each PlanStep object "
                "providing a Natural Language Data Mapping Directive (e.g. 'Extract total_inventory_value and set as amount') "
                "to guide runtime recovery if primary variable binding fails."
            )

        from src.core.llm_client import run_structured_llm
        plan_obj: Plan = run_structured_llm(
            prompt_name="planner_prompt.md",
            prompt_variables={
                "available_tools": json.dumps(available_tools_metadata, indent=2),
                "binding_instruction": binding_instruction,
                "fallback_instruction": fallback_instruction,
                "user_query": user_query
            },
            schema=Plan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model
        )
        return plan_obj
