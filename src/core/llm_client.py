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
    Centralized, provider-agnostic LLM client factory.
    Supports parsing models with a provider prefix:
    - "gemini/gemini-2.5-flash" or just "gemini-2.5-flash" (defaults to Gemini)
    - "openai/gpt-4o"
    - "anthropic/claude-3-5-sonnet"
    """
    provider = "gemini"
    name = model_name

    if "/" in model_name:
        provider, name = model_name.split("/", 1)

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required to instantiate the Gemini LLM client.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=name,
            google_api_key=api_key,
            temperature=temperature
        )
    elif provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is required to instantiate OpenAI client.")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=name, api_key=openai_key, temperature=temperature)
    elif provider == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required to instantiate Anthropic client.")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=name, api_key=anthropic_key, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


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

    # Load prompt text and create prompt template
    prompt_text = load_prompt_template(prompt_name)
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
