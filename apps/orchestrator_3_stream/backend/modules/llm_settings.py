"""
LLM Provider Runtime Settings

Centralizes provider metadata (Z.AI, Anthropic, OpenRouter) and exposes a shared
runtime state so the orchestrator, command agents, and stateless helpers all use
the same models and environment overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os

from . import config


@dataclass
class ProviderDefinition:
    """Static metadata describing an LLM provider option."""

    id: str
    label: str
    description: str
    default_model: str
    fast_model: str
    available_models: List[str]
    tags: List[str]
    icon: str
    docs_url: Optional[str] = None
    required_env: Optional[List[str]] = None


@dataclass
class RuntimeSettings:
    """Runtime selection shared across orchestrator + agents."""

    provider_id: str
    provider_label: str
    orchestrator_model: str
    default_agent_model: str
    fast_model: str
    env_overrides: Dict[str, str]
    updated_at: str

    def public_dict(self) -> Dict[str, Any]:
        """Serialize without leaking environment overrides."""
        return {
            "provider_id": self.provider_id,
            "provider_label": self.provider_label,
            "orchestrator_model": self.orchestrator_model,
            "default_agent_model": self.default_agent_model,
            "fast_model": self.fast_model,
            "updated_at": self.updated_at,
        }

    def to_metadata(self) -> Dict[str, Any]:
        """Metadata blob persisted on orchestrator row (no secrets)."""
        return self.public_dict()


# ---------------------------------------------------------------------------
# Provider catalog
# ---------------------------------------------------------------------------

PROVIDERS: Dict[str, ProviderDefinition] = {
    "zai": ProviderDefinition(
        id="zai",
        label="Z.AI",
        description="Anthropic-compatible endpoint with GLM 4.5 models.",
        default_model=config.DEFAULT_SONNET_MODEL,
        fast_model=config.FAST_MODEL,
        available_models=list(config.AVAILABLE_MODELS),
        tags=["Anthropic API", "Streaming", "GLM 4.5"],
        icon="⚡️",
        docs_url="https://z.ai/",
        required_env=["ANTHROPIC_AUTH_TOKEN"],
    ),
    "anthropic": ProviderDefinition(
        id="anthropic",
        label="Anthropic",
        description="Direct access to Claude models via api.anthropic.com.",
        default_model="claude-sonnet-4-5-20250929",
        fast_model="claude-haiku-4-5-20251001",
        available_models=[
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-5-20251017",
        ],
        tags=["Anthropic API", "First-party"],
        icon="🧠",
        docs_url="https://docs.anthropic.com/",
        required_env=["ANTHROPIC_API_KEY"],
    ),
    "openrouter": ProviderDefinition(
        id="openrouter",
        label="OpenRouter",
        description="Unified access to 50+ models including Claude, GPT, Gemini, Llama, Mistral, and more.",
        default_model="anthropic/claude-3.5-sonnet",
        fast_model="microsoft/phi-3-mini-128k-instruct",
        available_models=[
            # Anthropic Models
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3.5-haiku",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",

            # OpenAI Models
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",

            # Google/DeepMind Models
            "google/gemini-2.0-flash-exp",
            "google/gemini-1.5-pro",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-flash-8b",
            "google/gemini-pro",
            "google/gemini-pro-vision",

            # Meta Models
            "meta-llama/llama-3.1-405b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "meta-llama/llama-3-70b-instruct",
            "meta-llama/llama-3-8b-instruct",
            "meta-llama/llama-2-70b-chat",

            # Mistral Models
            "mistralai/mistral-large",
            "mistralai/mistral-medium",
            "mistralai/mistral-small",
            "mistralai/mistral-7b-instruct",
            "mistralai/mixtral-8x7b-instruct",
            "mistralai/mixtral-8x22b-instruct",

            # Microsoft Models
            "microsoft/phi-3-mini-128k-instruct",
            "microsoft/phi-3-medium-14b-instruct",
            "microsoft/wizardlm-2-8x22b",

            # Cohere Models
            "cohere/command-r-plus",
            "cohere/command-r",
            "cohere/command",
            "cohere/command-nightly",
            "cohere/command-light",

            # AI21 Labs Models
            "ai21/jamba-instruct",
            "ai21/jurassic-2-ultra",

            # Stability AI Models
            "stabilityai/stablelm-2-12b-chat",
            "stabilityai/stable-code-instruct",

            # X-AI Models
            "x-ai/grok-2",
            "x-ai/grok-2-mini",
            "x-ai/grok-2-vision",

            # Qwen Models (Alibaba)
            "qwen/qwen-2.5-72b-instruct",
            "qwen/qwen-2.5-32b-instruct",
            "qwen/qwen-2.5-14b-instruct",
            "qwen/qwen-2.5-7b-instruct",
            "qwen/qwen-2-72b-instruct",

            # Yi Models (01.AI)
            "01-ai/yi-large",
            "01-ai/yi-medium",
            "01-ai/yi-small",
            "01-ai/yi-34b-chat",

            # DeepSeek Models
            "deepseek/deepseek-chat",
            "deepseek/deepseek-coder",

            # Wizard Models
            "wizardlm/wizardlm-2-8x22b",
            "wizardlm/wizardlm-70b",

            # Solar Models (Upstage)
            "upstage/solar-1-mini-chat",
            "upstage/solar-pro",

            # Nvidia Models
            "nvidia/nemotron-4-340b-instruct",

            # Dbrx Models
            "databricks/dbrx-instruct",

            # Groq Models (Fast inference)
            "groq/llama-3.1-70b-versatile",
            "groq/llama-3.1-8b-instant",
            "groq/mixtral-8x7b-32768",

            # Together AI Models
            "togethercomputer/llama-3.1-405b-instruct",
            "togethercomputer/stripedhyena-nous-7b",

            # Perplexity Models
            "perplexity/llama-3.1-sonar-small-128k-chat",
            "perplexity/llama-3.1-sonar-large-128k-chat",

            # Specialized Models
            "openchat/openchat-7b",
            "phind/phind-code-llama-34b-v2",
            "undi95/toppy-m-7b",
            "gryphe/mythomist-7b",
            "teknium/openhermes-2.5-mistral-7b",
        ],
        tags=[
            "OpenRouter",
            "Multi-provider",
            "Claude",
            "GPT",
            "Gemini",
            "Llama",
            "Mistral",
            "Cohere",
            "Open Source",
            "Commercial",
            "Fast Inference",
            "Code Generation",
            "Chat",
            "Streaming"
        ],
        icon="🚀",
        docs_url="https://openrouter.ai/docs",
        required_env=["OPENROUTER_API_KEY"],
    ),
}


_runtime_settings: Optional[RuntimeSettings] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_provider(provider_id: str) -> ProviderDefinition:
    provider = PROVIDERS.get(provider_id.lower())
    if not provider:
        raise ValueError(f"Unknown LLM provider '{provider_id}'")
    return provider


def _resolve_model_name(model_name: Optional[str], provider: ProviderDefinition) -> str:
    if not model_name:
        return provider.default_model
    # Allow aliases defined in config, otherwise pass-through
    return config.resolve_model_alias(model_name)


def _build_env_overrides(provider_id: str) -> Dict[str, str]:
    """Derive provider-specific env vars without exposing secrets to clients."""
    overrides: Dict[str, str] = {}
    provider_id = provider_id.lower()

    if provider_id == "zai":
        token = os.getenv("ZAI_ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        base_url = (
            os.getenv("ZAI_ANTHROPIC_BASE_URL")
            or os.getenv("ANTHROPIC_BASE_URL")
            or "https://api.z.ai/api/anthropic"
        )
        if token:
            overrides["ANTHROPIC_AUTH_TOKEN"] = token
            overrides["ANTHROPIC_API_KEY"] = token
        overrides["ANTHROPIC_BASE_URL"] = base_url
    elif provider_id == "anthropic":
        token = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        if token:
            overrides["ANTHROPIC_API_KEY"] = token
            overrides.setdefault("ANTHROPIC_AUTH_TOKEN", token)
        overrides["ANTHROPIC_BASE_URL"] = base_url
    elif provider_id == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        if key:
            overrides["OPENROUTER_API_KEY"] = key
        overrides["OPENROUTER_BASE_URL"] = base_url
        site_url = os.getenv("OPENROUTER_SITE_URL")
        site_name = os.getenv("OPENROUTER_SITE_NAME")
        if site_url:
            overrides["OPENROUTER_SITE_URL"] = site_url
        if site_name:
            overrides["OPENROUTER_SITE_NAME"] = site_name

    return overrides


def _build_runtime(
    provider: ProviderDefinition,
    orchestrator_model: Optional[str],
    default_agent_model: Optional[str],
    fast_model: Optional[str],
) -> RuntimeSettings:
    """Create a runtime settings instance with alias resolution + env overrides."""
    resolved_orch = _resolve_model_name(orchestrator_model, provider)
    resolved_default = _resolve_model_name(default_agent_model, provider)
    resolved_fast = _resolve_model_name(fast_model or provider.fast_model, provider)

    return RuntimeSettings(
        provider_id=provider.id,
        provider_label=provider.label,
        orchestrator_model=resolved_orch,
        default_agent_model=resolved_default,
        fast_model=resolved_fast,
        env_overrides=_build_env_overrides(provider.id),
        updated_at=_now_iso(),
    )


def initialize_runtime(metadata: Optional[Dict[str, Any]] = None) -> RuntimeSettings:
    """
    Bootstraps runtime settings from orchestrator metadata or environment.
    Should be called once during FastAPI lifespan startup.
    """
    metadata = metadata or {}
    provider_meta = metadata.get("llm_provider") or {}
    provider_id = provider_meta.get("provider_id") or config.DEFAULT_LLM_PROVIDER

    try:
        provider = _get_provider(provider_id)
    except ValueError:
        provider = _get_provider("zai")
    runtime = _build_runtime(
        provider=provider,
        orchestrator_model=provider_meta.get("orchestrator_model"),
        default_agent_model=provider_meta.get("default_agent_model"),
        fast_model=provider_meta.get("fast_model"),
    )

    set_runtime(runtime)
    return runtime


def set_runtime(runtime: RuntimeSettings) -> RuntimeSettings:
    """Update module-level runtime settings."""
    global _runtime_settings
    _runtime_settings = runtime
    return runtime


def apply_provider_selection(
    provider_id: str,
    orchestrator_model: Optional[str] = None,
    default_agent_model: Optional[str] = None,
    fast_model: Optional[str] = None,
) -> RuntimeSettings:
    """Create + store runtime settings for a provider selection."""
    provider = _get_provider(provider_id)
    runtime = _build_runtime(provider, orchestrator_model, default_agent_model, fast_model)
    return set_runtime(runtime)


def get_runtime_settings() -> RuntimeSettings:
    if _runtime_settings is None:
        # Should not happen, but fall back to defaults
        initialize_runtime({})
    return _runtime_settings  # type: ignore[return-value]


def get_orchestrator_model() -> str:
    return get_runtime_settings().orchestrator_model


def get_default_agent_model() -> str:
    return get_runtime_settings().default_agent_model


def get_fast_model() -> str:
    return get_runtime_settings().fast_model


def build_runtime_env() -> Dict[str, str]:
    """
    Base Claude env vars + provider overrides.
    Tokens remain server-side and are never returned to the UI.
    """
    env = config.build_llm_env()
    env.update(get_runtime_settings().env_overrides)
    return env


def list_providers() -> List[Dict[str, Any]]:
    """Return provider catalog with readiness info (no secrets)."""
    providers = []
    for provider in PROVIDERS.values():
        missing = []
        if provider.id == "zai":
            if not (os.getenv("ZAI_ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
                missing.append("ANTHROPIC_AUTH_TOKEN")
        elif provider.required_env:
            for key in provider.required_env:
                if not os.getenv(key):
                    missing.append(key)

        providers.append(
            {
                "id": provider.id,
                "label": provider.label,
                "description": provider.description,
                "icon": provider.icon,
                "tags": provider.tags,
                "default_model": provider.default_model,
                "fast_model": provider.fast_model,
                "available_models": provider.available_models,
                "docs_url": provider.docs_url,
                "is_ready": len(missing) == 0,
                "missing_keys": missing,
            }
        )
    return providers


def serialize_runtime() -> Dict[str, Any]:
    """Expose runtime selection without env overrides."""
    return get_runtime_settings().public_dict()
