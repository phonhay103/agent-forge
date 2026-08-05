from typing import List, Any, Union, Optional
from json_schema_binder import BaseBindingEngine, get_binding_engine
from pydantic import BaseModel, Field
import json
import pathlib
import os

from src.agent.models import UnifiedPlan
from prompt_composer import PromptComposer
from src.shared.llm_client import run_structured_llm

DEFAULT_BINDING_FAILED_TOKEN = os.getenv("BINDING_FAILED_TOKEN", "__BINDING_FAILED__")
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"

class UnifiedPlanner:
    def __init__(
        self,
        model: Optional[Any] = None,
        model_name: str = "gemini-2.5-flash",
        binding_failed_token: Optional[str] = None,
        prompt: Optional[PromptComposer] = None,
        # Feature flags
        use_pre_planned_jmespath: bool = False,
    ):
        self.model = model
        self.model_name = model_name
        self.binding_failed_token = binding_failed_token or DEFAULT_BINDING_FAILED_TOKEN
        self.prompt = prompt
        self.use_pre_planned_jmespath = use_pre_planned_jmespath

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
        binding_type: Union[str, BaseBindingEngine] = "jmespath",
        enable_llm_fallback: bool = False,
    ) -> UnifiedPlan:
        from src.shared.llm_client import run_structured_llm

        if self.use_pre_planned_jmespath:
            # Dynamic / Hybrid mapping mode
            prompt = self.prompt or PromptComposer.from_file("planner_prompt_dynamic.yaml", PROMPTS_DIR)
            prompt.set_variable("available_tools", json.dumps(available_tools_metadata, indent=2))
            prompt_text = prompt.render()

            plan_obj: UnifiedPlan = run_structured_llm(
                prompt_text=prompt_text,
                prompt_variables={"user_query": user_query},
                schema=UnifiedPlan,
                model_name=self.model_name,
                temperature=0.0,
                base_model=self.model,
            )
            return plan_obj

        else:
            # Static binding mode
            engine = get_binding_engine(binding_type) if isinstance(binding_type, str) else binding_type
            binding_instruction = engine.get_system_prompt_instruction()
            regex_pattern = engine.get_regex_pattern() if hasattr(engine, "get_regex_pattern") else None

            prompt = self.prompt or PromptComposer.from_file("planner_prompt_static.yaml", PROMPTS_DIR)
            prompt.set_variable("available_tools", json.dumps(available_tools_metadata, indent=2))
            prompt.set_variable("binding_instruction", binding_instruction)
            prompt.set_variable("binding_failed_token", self.binding_failed_token)
            
            prompt_text = prompt.render()

            plan_obj: UnifiedPlan = run_structured_llm(
                prompt_text=prompt_text,
                prompt_variables={
                    "user_query": user_query
                },
                schema=UnifiedPlan,
                model_name=self.model_name,
                temperature=0.0,
                base_model=self.model
            )

            if regex_pattern:
                plan_obj = UnifiedPlan.model_validate(plan_obj.model_dump(), context={"regex_pattern": regex_pattern})

            return plan_obj


class Planner(UnifiedPlanner):
    def __init__(
        self,
        model: Optional[Any] = None,
        model_name: str = "gemini-2.5-flash",
        binding_failed_token: Optional[str] = None,
        prompt: Optional[PromptComposer] = None,
    ):
        super().__init__(
            model=model,
            model_name=model_name,
            binding_failed_token=binding_failed_token,
            prompt=prompt,
            use_pre_planned_jmespath=False,
        )

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
        binding_type: Union[str, BaseBindingEngine] = "jmespath",
        enable_llm_fallback: bool = False,
    ) -> UnifiedPlan:
        engine = get_binding_engine(binding_type) if isinstance(binding_type, str) else binding_type
        binding_instruction = engine.get_system_prompt_instruction()
        regex_pattern = engine.get_regex_pattern() if hasattr(engine, "get_regex_pattern") else None

        prompt = self.prompt or PromptComposer.from_file("planner_prompt_static.yaml", PROMPTS_DIR)
        prompt.set_variable("available_tools", json.dumps(available_tools_metadata, indent=2))
        prompt.set_variable("binding_instruction", binding_instruction)
        prompt.set_variable("binding_failed_token", self.binding_failed_token)
        
        prompt_text = prompt.render()

        plan_obj: UnifiedPlan = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={
                "user_query": user_query
            },
            schema=UnifiedPlan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model
        )

        if regex_pattern:
            plan_obj = UnifiedPlan.model_validate(plan_obj.model_dump(), context={"regex_pattern": regex_pattern})

        return plan_obj


class DynamicPlanner(UnifiedPlanner):
    def __init__(
        self,
        model: Optional[Any] = None,
        model_name: str = "gemini-2.5-flash",
        prompt: Optional[PromptComposer] = None,
    ):
        super().__init__(
            model=model,
            model_name=model_name,
            prompt=prompt,
            use_pre_planned_jmespath=True,
        )

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
    ) -> UnifiedPlan:
        prompt = self.prompt or PromptComposer.from_file("planner_prompt_dynamic.yaml", PROMPTS_DIR)
        prompt.set_variable("available_tools", json.dumps(available_tools_metadata, indent=2))
        prompt_text = prompt.render()

        plan_obj: UnifiedPlan = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={"user_query": user_query},
            schema=UnifiedPlan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model,
        )
        return plan_obj
