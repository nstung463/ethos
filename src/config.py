"""LLM configuration — multi-provider via init_chat_model.

Supports:
- Native providers via ``init_chat_model`` (e.g. anthropic, openai)
- Common aliases to native providers:
  gemini -> google_genai, amazon -> bedrock, azure -> azure_openai
- Popular OpenAI-compatible providers via aliases:
  openrouter, deepseek, together, groq, xai, fireworks, perplexity
"""

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from src.logger import get_logger

logger = get_logger(__name__)

PROVIDER_ALIASES = {
    "gemini": "google_genai",
    "google": "google_genai",
    "amazon": "bedrock",
    "bedrock": "bedrock",
    "azure": "azure_openai",
}

OPENAI_COMPATIBLE_PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "base_url_env": "OPENROUTER_BASE_URL",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "base_url_env": "TOGETHER_BASE_URL",
        "api_key_env": "TOGETHER_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "base_url_env": "GROQ_BASE_URL",
        "api_key_env": "GROQ_API_KEY",
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "base_url_env": "XAI_BASE_URL",
        "api_key_env": "XAI_API_KEY",
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "base_url_env": "FIREWORKS_BASE_URL",
        "api_key_env": "FIREWORKS_API_KEY",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "base_url_env": "PERPLEXITY_BASE_URL",
        "api_key_env": "PERPLEXITY_API_KEY",
    },
}


def get_model() -> BaseChatModel:
    """Resolve the LLM from environment variables.

    Uses ETHOS_PROVIDER (default: anthropic) and ETHOS_MODEL (default: claude-sonnet-4-6).
    Supports any provider/model combo accepted by init_chat_model, e.g.:
      - anthropic:claude-sonnet-4-6
      - openai:gpt-4o
      - gemini:gemini-2.5-pro (alias -> google_genai)
      - amazon:anthropic.claude-3-5-sonnet-20240620-v1:0 (alias -> bedrock)
      - azure:gpt-4o (alias -> azure_openai)
      - openrouter:openai/gpt-4o-mini
      - deepseek:deepseek-chat
    """
    provider = os.getenv("ETHOS_PROVIDER", "anthropic").strip().lower()
    provider = PROVIDER_ALIASES.get(provider, provider)
    model = os.getenv("ETHOS_MODEL", "claude-sonnet-4-6")
    logger.info("Resolving model configuration (provider=%s, model=%s)", provider, model)
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        conf = OPENAI_COMPATIBLE_PROVIDERS[provider]
        base_url = os.getenv(conf["base_url_env"], conf["base_url"])
        api_key = os.getenv(conf["api_key_env"], "")
        kwargs: dict[str, str | float] = {
            "base_url": base_url,
            "temperature": 0.0,
        }
        if api_key:
            kwargs["api_key"] = api_key
        logger.debug("Using OpenAI-compatible provider base_url=%s", base_url)
        return init_chat_model(f"openai:{model}", **kwargs)

    return init_chat_model(f"{provider}:{model}", temperature=0.0)


def get_workspace() -> str:
    """Return the workspace root directory."""
    return os.getenv("ETHOS_WORKSPACE", "./workspace")
