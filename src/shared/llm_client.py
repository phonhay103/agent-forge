import functools
import os
from typing import Any


@functools.lru_cache(maxsize=16)
def get_llm_client(model_name: str = "gemini-2.5-flash", temperature: float = 0.0) -> Any:
    """
    Centralized, provider-agnostic LLM client factory using native LangChain SDK.
    Supports parsing models with a provider prefix (using '/' or ':'):
    - "gemini/gemini-2.5-flash" or just "gemini-2.5-flash" (defaults to google_genai)
    - "openai/gpt-4o"
    - "anthropic/claude-3-5-sonnet"
    - "cohere/command-r"
    - "openrouter/anthropic/claude-3.5-sonnet"
    """
    from langchain.chat_models import init_chat_model

    provider = "gemini"
    name = model_name

    # Special handling for openrouter since model names contain slashes (e.g., anthropic/claude-3.5-sonnet)
    if model_name.lower().startswith("openrouter/") or model_name.lower().startswith("openrouter:"):
        provider = "openrouter"
        name = model_name[11:]
    elif "/" in model_name:
        provider, name = model_name.split("/", 1)
    elif ":" in model_name:
        provider, name = model_name.split(":", 1)

    # Normalize/Map provider alias to standard LangChain provider names
    provider_mapping = {
        "gemini": "google_genai",
        "google": "google_genai",
        "google_genai": "google_genai",
        "openai": "openai",
        "anthropic": "anthropic",
        "cohere": "cohere",
        "mistral": "mistralai",
        "mistralai": "mistralai",
        "groq": "groq",
        "ollama": "ollama",
        "openrouter": "openrouter",
    }

    mapped_provider = provider_mapping.get(provider.lower(), provider.lower())

    # Pre-flight credential checks for major providers to assist developer onboarding
    if mapped_provider == "google_genai" and not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable is required to instantiate the Gemini LLM client.")
    elif mapped_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required to instantiate the OpenAI LLM client.")
    elif mapped_provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is required to instantiate the Anthropic LLM client.")
    elif mapped_provider == "openrouter" and not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError("OPENROUTER_API_KEY environment variable is required to instantiate the OpenRouter LLM client.")

    # Initialize the chat model natively and agnostically
    return init_chat_model(
        model=name,
        model_provider=mapped_provider,
        temperature=temperature
    )


def get_structured_llm_client(
    schema: Any,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    base_model: Any | None = None
) -> Any:
    """
    Centralized factory for structured LLM clients.
    Binds the requested schema or Pydantic model to the LLM client.
    """
    llm = base_model if base_model is not None else get_llm_client(model_name=model_name, temperature=temperature)
    return llm.with_structured_output(schema)


def run_structured_llm(
    prompt_text: str,
    prompt_variables: dict[str, Any],
    schema: Any,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    base_model: Any | None = None
) -> Any:
    """
    Centralized execution of structured LLM chains.
    Binds the structured schema, creates and runs the chain pipeline.
    """
    from langchain_core.messages import SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

    if "user_query" in prompt_variables:
        prompt_template = ChatPromptTemplate([
            SystemMessage(content=prompt_text),
            HumanMessagePromptTemplate.from_template("{user_query}")
        ])
    else:
        from langchain_core.messages import HumanMessage
        prompt_template = ChatPromptTemplate([
            SystemMessage(content=prompt_text),
            HumanMessage(content="Generate the requested structured output.")
        ])

    # Resolve structured model client
    structured_llm = get_structured_llm_client(
        schema=schema,
        model_name=model_name,
        temperature=temperature,
        base_model=base_model
    )

    # Build and run the LCEL pipeline chain
    chain = prompt_template | structured_llm
    return chain.invoke(prompt_variables)
