from typing import List, Any, Union, Optional
from json_schema_binder import BaseBindingEngine, get_binding_engine
from pydantic import BaseModel, Field
import json
import pathlib
import os

from src.static_agent.models import PlanTask, Plan
from prompt_composer import PromptComposer

DEFAULT_BINDING_FAILED_TOKEN = os.getenv("BINDING_FAILED_TOKEN", "__BINDING_FAILED__")
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"

class Planner:
    def __init__(
        self,
        model: Optional[Any] = None,
        model_name: str = "gemini-2.5-flash",
        binding_failed_token: Optional[str] = None
    ):
        self.model = model
        self.model_name = model_name
        self.binding_failed_token = binding_failed_token or DEFAULT_BINDING_FAILED_TOKEN

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
        binding_type: Union[str, BaseBindingEngine] = "jmespath",
        enable_llm_fallback: bool = False
    ) -> Plan:
        engine = get_binding_engine(binding_type) if isinstance(binding_type, str) else binding_type
        binding_instruction = engine.get_system_prompt_instruction()
        regex_pattern = engine.get_regex_pattern() if hasattr(engine, "get_regex_pattern") else None

        fallback_instruction = ""
        if enable_llm_fallback:
            fallback_instruction = (
                "\nLLM FALLBACK MODE IS ENABLED.\n"
                "For tasks referencing previous task outputs, generate a 'directive' field in each PlanTask object "
                "providing a Natural Language Data Mapping Directive (e.g. 'Extract total_inventory_value and set as amount') "
                "to guide runtime recovery if primary variable binding fails."
            )

        from src.shared.llm_client import run_structured_llm
        
        prompt = PromptComposer.from_file("planner_prompt.md", PROMPTS_DIR)
        prompt.set_slot("available_tools", json.dumps(available_tools_metadata, indent=2))
        prompt.set_slot("binding_instruction", binding_instruction)
        prompt.set_slot("binding_failed_token", self.binding_failed_token)
        prompt.set_slot("fallback_instruction", fallback_instruction)
        
        prompt_text = prompt.render()

        plan_obj: Plan = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={
                "user_query": user_query
            },
            schema=Plan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model
        )

        if regex_pattern:
            plan_obj = Plan.model_validate(plan_obj.model_dump(), context={"regex_pattern": regex_pattern})

        return plan_obj
