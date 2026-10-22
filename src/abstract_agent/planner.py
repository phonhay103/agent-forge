import pathlib
from typing import Any

from prompt_composer import PromptComposer
from src.abstract_agent.models import AbstractPlan
from src.shared.llm_client import run_structured_llm

PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


class AbstractPlanner:
    """
    Planner that only describes tasks/intents.
    Does NOT select specific tools — runtime handles that.
    """

    def __init__(
        self, model: Any | None = None, model_name: str = "gemini-2.5-flash", prompt: PromptComposer | None = None
    ) -> None:
        self.model = model
        self.model_name = model_name
        self.prompt = prompt

    def create_plan(
        self,
        user_query: str,
        available_tools_metadata: list[Any],
    ) -> AbstractPlan:
        prompt = self.prompt or PromptComposer.from_file(
            "abstract_planner_prompt.yaml", PROMPTS_DIR, template_format="yaml"
        )
        capabilities = self._summarize_capabilities(available_tools_metadata)
        prompt.set_variable("available_capabilities", capabilities)
        prompt_text = prompt.render()

        plan_obj: AbstractPlan = run_structured_llm(
            prompt_text=prompt_text,
            prompt_variables={"user_query": user_query},
            schema=AbstractPlan,
            model_name=self.model_name,
            temperature=0.0,
            base_model=self.model,
        )
        return plan_obj

    def _summarize_capabilities(self, tools_metadata: list[Any]) -> str:
        """Create a high-level summary of available capabilities without exposing full tool schemas."""
        summaries = []
        for t in tools_metadata:
            name = t.get("name", "unknown")
            desc = t.get("description", "No description")
            summaries.append(f"- {name}: {desc}")
        return "\n".join(summaries)
