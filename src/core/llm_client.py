import os
import pathlib
import functools
from typing import Any, Optional

@functools.lru_cache(maxsize=32)
def load_prompt_template(name: str) -> str:
    """
    Loads prompt templates from the centralized prompts directory.
    Ensures safe path resolution from any execution directory.
    """
    base_dir = pathlib.Path(__file__).parent
    prompt_path = base_dir / "prompts" / name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

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
    if model_name.lower().startswith("openrouter/"):
        provider = "openrouter"
        name = model_name[11:]
    elif model_name.lower().startswith("openrouter:"):
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
    base_model: Optional[Any] = None
) -> Any:
    """
    Centralized factory for structured LLM clients.
    Binds the requested schema or Pydantic model to the LLM client.
    """
    llm = base_model if base_model is not None else get_llm_client(model_name=model_name, temperature=temperature)
    return llm.with_structured_output(schema)


def run_structured_llm(
    prompt_name: str,
    prompt_variables: dict,
    schema: Any,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    base_model: Optional[Any] = None
) -> Any:
    """
    Centralized execution of structured LLM chains.
    Loads the prompt, binds the structured schema, creates and runs the chain pipeline.
    """
    from langchain_core.prompts import ChatPromptTemplate

    # Load prompt text and create native ChatPromptTemplate with System & Human message roles
    prompt_text = load_prompt_template(prompt_name)
    if "user_query" in prompt_variables:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", "{user_query}")
        ])
    else:
        prompt_template = ChatPromptTemplate.from_template(prompt_text)

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
