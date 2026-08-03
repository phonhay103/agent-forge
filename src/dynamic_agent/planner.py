import json
import pathlib
from typing import List, Any, Optional

from prompt_composer import PromptComposer

from src.dynamic_agent.models import DynamicPlan
from src.shared.llm_client import run_structured_llm

PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


class DynamicPlanner:
    """
    Planner that selects tools and execution order (DAG),
    but does NOT write variable binding expressions.
    """

    def __init__(self, model: Optional[Any] = None, model_name: str = "gemini-2.5-flash"):
        self.model = model
        self.model_name = model_name

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: List[Any],
    ) -> DynamicPlan:
        prompt = PromptComposer.from_file("dynamic_planner_prompt.yaml", PROMPTS_DIR)
        prompt.set_slot("available_tools", json.dumps(available_tools_metadata, indent=2))
        prompt_text = prompt.render()

        plan_obj: DynamicPlan = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={"user_query": user_query},
            schema=DynamicPlan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model,
        )
        return plan_obj
