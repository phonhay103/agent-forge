import os
from unittest.mock import patch

import pytest

from src.shared.llm_client import get_llm_client


def test_get_llm_client_google_genai():
    # Clear cache to ensure tests run with mock environments
    get_llm_client.cache_clear()
    with patch("langchain.chat_models.init_chat_model") as mock_init:
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            get_llm_client("gemini-2.5-flash", temperature=0.5)
            mock_init.assert_called_once_with(model="gemini-2.5-flash", model_provider="google_genai", temperature=0.5)


def test_get_llm_client_openai():
    get_llm_client.cache_clear()
    with patch("langchain.chat_models.init_chat_model") as mock_init:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            get_llm_client("openai/gpt-4o", temperature=0.2)
            mock_init.assert_called_once_with(model="gpt-4o", model_provider="openai", temperature=0.2)


def test_get_llm_client_anthropic():
    get_llm_client.cache_clear()
    with patch("langchain.chat_models.init_chat_model") as mock_init:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            get_llm_client("anthropic:claude-3-5-sonnet", temperature=0.1)
            mock_init.assert_called_once_with(model="claude-3-5-sonnet", model_provider="anthropic", temperature=0.1)


def test_get_llm_client_openrouter():
    get_llm_client.cache_clear()
    with patch("langchain.chat_models.init_chat_model") as mock_init:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            get_llm_client("openrouter/anthropic/claude-3-5-sonnet", temperature=0.3)
            mock_init.assert_called_once_with(
                model="anthropic/claude-3-5-sonnet", model_provider="openrouter", temperature=0.3
            )


def test_get_llm_client_missing_key():
    get_llm_client.cache_clear()
    with patch.dict(os.environ, {}):
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
            get_llm_client("gemini-2.5-flash")

    from src.agent.models import Plan, PlanTask as PlanStep

    step = PlanStep(id="task_1", tool_name="some_tool", args={}, reason="Because we need to query search")
    plan = Plan(tasks=[step], reason="This plan converts searched products.")
    assert plan.reason == "This plan converts searched products."
    assert plan.tasks[0].reason == "Because we need to query search"
