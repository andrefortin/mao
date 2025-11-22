"""
OpenRouter Models Module

Dynamic model loading and management for OpenRouter API with comprehensive
model information, caching, filtering capabilities, and provider categorization.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib

import httpx
from pydantic import BaseModel, Field, validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelCapability(str, Enum):
    """Model capabilities for filtering and categorization."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    VISION = "vision"
    AUDIO = "audio"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    IMAGE_GENERATION = "image_generation"
    EMBEDDINGS = "embeddings"
    MODERATION = "moderation"


class ProviderCategory(str, Enum):
    """Provider categories for organization."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    META = "meta"
    MISTRAL = "mistral"
    COHERE = "cohere"
    XAI = "xai"
    PERPLEXITY = "perplexity"
    STABILITY = "stability"
    REKA = "reka"
    FIREWORKS = "fireworks"
    TOGETHER = "together"
    NOVA = "nova"
    OTHER = "other"


class ModelSize(str, Enum):
    """Model size categories."""
    TINY = "tiny"      # < 1B parameters
    SMALL = "small"    # 1B - 7B parameters
    MEDIUM = "medium"  # 8B - 35B parameters
    LARGE = "large"    # 36B - 100B parameters
    XLARGE = "xlarge"  # 100B+ parameters


class OpenRouterError(Exception):
    """Base exception for OpenRouter model operations."""
    pass


class ModelFetchError(OpenRouterError):
    """Exception raised when model fetching fails."""
    pass


class ModelValidationError(OpenRouterError):
    """Exception raised when model validation fails."""
    pass


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    model_id: str
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal
    cache_read_cost_per_million: Optional[Decimal] = None
    cache_write_cost_per_million: Optional[Decimal] = None
    context_window: Optional[int] = None
    provider: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def calculate_cost(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0
    ) -> Decimal:
        """Calculate total cost based on token usage."""
        cost = Decimal('0')

        if input_tokens > 0:
            cost += (Decimal(input_tokens) / Decimal('1000000')) * self.input_cost_per_million

        if output_tokens > 0:
            cost += (Decimal(output_tokens) / Decimal('1000000')) * self.output_cost_per_million

        if cache_read_tokens > 0 and self.cache_read_cost_per_million:
            cost += (Decimal(cache_read_tokens) / Decimal('1000000')) * self.cache_read_cost_per_million

        if cache_write_tokens > 0 and self.cache_write_cost_per_million:
            cost += (Decimal(cache_write_tokens) / Decimal('1000000')) * self.cache_write_cost_per_million

        return cost


class OpenRouterModel(BaseModel):
    """Comprehensive model information from OpenRouter."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="Provider name")
    description: Optional[str] = Field(None, description="Model description")

    # Capabilities
    capabilities: Set[ModelCapability] = Field(
        default_factory=set,
        description="Model capabilities"
    )

    # Technical specifications
    context_length: Optional[int] = Field(None, description="Maximum context length")
    max_tokens: Optional[int] = Field(None, description="Maximum output tokens")
    input_limit: Optional[int] = Field(None, description="Input token limit")

    # Pricing
    pricing: Optional[ModelPricing] = Field(None, description="Pricing information")

    # Model characteristics
    architecture: Optional[str] = Field(None, description="Model architecture")
    model_size: Optional[ModelSize] = Field(None, description="Model size category")
    training_data_cutoff: Optional[datetime] = Field(None, description="Training data cutoff date")

    # Metadata
    tags: Set[str] = Field(default_factory=set, description="Model tags")
    category: Optional[str] = Field(None, description="Model category")
    is_open_source: bool = Field(False, description="Whether model is open source")
    is_available: bool = Field(True, description="Whether model is currently available")

    # API information
    api_endpoint: Optional[str] = Field(None, description="API endpoint")
    requires_special_header: bool = Field(False, description="Whether special headers are required")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Model creation date")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    @validator('capabilities', pre=True)
    def parse_capabilities(cls, v):
        """Parse capabilities from various input formats."""
        if isinstance(v, str):
            return {ModelCapability(cap) for cap in v.split(',')}
        elif isinstance(v, list):
            return {ModelCapability(cap) for cap in v}
        elif isinstance(v, set):
            return {ModelCapability(cap) for cap in v}
        return v

    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """Parse tags from various input formats."""
        if isinstance(v, str):
            return set(tag.strip() for tag in v.split(',') if tag.strip())
        elif isinstance(v, list):
            return set(tag for tag in v)
        return v

    @validator('training_data_cutoff', pre=True)
    def parse_training_cutoff(cls, v):
        """Parse training data cutoff from string or timestamp."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        return datetime.strptime(v, fmt)
                    except ValueError:
                        continue
                return None
        return v

    def get_provider_category(self) -> ProviderCategory:
        """Get provider category from provider string."""
        provider_lower = self.provider.lower()

        if 'anthropic' in provider_lower:
            return ProviderCategory.ANTHROPIC
        elif 'openai' in provider_lower:
            return ProviderCategory.OPENAI
        elif 'google' in provider_lower:
            return ProviderCategory.GOOGLE
        elif 'meta' in provider_lower or 'llama' in provider_lower:
            return ProviderCategory.META
        elif 'mistral' in provider_lower:
            return ProviderCategory.MISTRAL
        elif 'cohere' in provider_lower:
            return ProviderCategory.COHERE
        elif 'x-ai' in provider_lower or 'grok' in provider_lower:
            return ProviderCategory.XAI
        elif 'perplexity' in provider_lower:
            return ProviderCategory.PERPLEXITY
        elif 'stability' in provider_lower:
            return ProviderCategory.STABILITY
        elif 'reka' in provider_lower:
            return ProviderCategory.REKA
        elif 'fireworks' in provider_lower:
            return ProviderCategory.FIREWORKS
        elif 'together' in provider_lower:
            return ProviderCategory.TOGETHER
        elif 'nova' in provider_lower:
            return ProviderCategory.NOVA
        else:
            return ProviderCategory.OTHER

    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if model supports a specific capability."""
        return capability in self.capabilities

    def estimate_cost(self, input_tokens: int = 0, output_tokens: int = 0) -> Optional[Decimal]:
        """Estimate cost for given token usage."""
        if not self.pricing:
            return None
        return self.pricing.calculate_cost(input_tokens, output_tokens)

    def is_fast_model(self) -> bool:
        """Determine if this is a fast/inexpensive model."""
        if not self.pricing:
            return False
        # Consider models under $1 per million input tokens as "fast"
        return self.pricing.input_cost_per_million < Decimal('1.0')

    def is_premium_model(self) -> bool:
        """Determine if this is a premium/expensive model."""
        if not self.pricing:
            return False
        # Consider models over $10 per million input tokens as "premium"
        return self.pricing.input_cost_per_million >= Decimal('10.0')


class ModelCache(BaseModel):
    """Cache for storing model information to reduce API calls."""

    cache_dir: Path = Field(default_factory=lambda: Path.home() / '.cache' / 'openrouter_models')
    cache_ttl: int = Field(3600, description="Cache time-to-live in seconds")
    max_cache_size: int = Field(1000, description="Maximum number of cached models")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        # Use hash for safe filename
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"models_{safe_key}.json"

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid."""
        if not cache_file.exists():
            return False

        file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        return file_age < self.cache_ttl

    async def get_cached_models(self, cache_key: str = "default") -> Optional[List[OpenRouterModel]]:
        """Get models from cache if available and valid."""
        cache_file = self._get_cache_file(cache_key)

        if not self._is_cache_valid(cache_file):
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            models = []
            for model_data in data:
                # Convert capabilities and tags back to sets
                if 'capabilities' in model_data and isinstance(model_data['capabilities'], list):
                    model_data['capabilities'] = set(model_data['capabilities'])
                if 'tags' in model_data and isinstance(model_data['tags'], list):
                    model_data['tags'] = set(model_data['tags'])

                # Parse pricing if present
                if 'pricing' in model_data and model_data['pricing']:
                    pricing_data = model_data['pricing']
                    # Convert string costs back to Decimal
                    for cost_field in ['input_cost_per_million', 'output_cost_per_million',
                                     'cache_read_cost_per_million', 'cache_write_cost_per_million']:
                        if pricing_data.get(cost_field):
                            pricing_data[cost_field] = Decimal(str(pricing_data[cost_field]))

                    # Parse datetime
                    if 'last_updated' in pricing_data:
                        pricing_data['last_updated'] = datetime.fromisoformat(pricing_data['last_updated'])

                    model_data['pricing'] = ModelPricing(**pricing_data)

                models.append(OpenRouterModel(**model_data))

            return models

        except Exception as e:
            # If cache is corrupted, ignore it
            cache_file.unlink(missing_ok=True)
            return None

    async def cache_models(self, models: List[OpenRouterModel], cache_key: str = "default") -> None:
        """Cache models to file."""
        cache_file = self._get_cache_file(cache_key)

        try:
            data = []
            for model in models:
                model_dict = model.model_dump()

                # Convert sets to lists for JSON serialization
                if isinstance(model_dict.get('capabilities'), set):
                    model_dict['capabilities'] = list(model_dict['capabilities'])
                if isinstance(model_dict.get('tags'), set):
                    model_dict['tags'] = list(model_dict['tags'])

                # Convert pricing to dict
                if model_dict.get('pricing'):
                    pricing = model.pricing
                    model_dict['pricing'] = {
                        'model_id': pricing.model_id,
                        'input_cost_per_million': str(pricing.input_cost_per_million),
                        'output_cost_per_million': str(pricing.output_cost_per_million),
                        'cache_read_cost_per_million': str(pricing.cache_read_cost_per_million) if pricing.cache_read_cost_per_million else None,
                        'cache_write_cost_per_million': str(pricing.cache_write_cost_per_million) if pricing.cache_write_cost_per_million else None,
                        'context_window': pricing.context_window,
                        'provider': pricing.provider,
                        'last_updated': pricing.last_updated.isoformat()
                    }

                # Convert datetime to ISO string
                if model_dict.get('training_data_cutoff'):
                    model_dict['training_data_cutoff'] = model.training_data_cutoff.isoformat()
                if model_dict.get('last_updated'):
                    model_dict['last_updated'] = model.last_updated.isoformat()
                if model_dict.get('created_at'):
                    model_dict['created_at'] = model.created_at.isoformat()

                data.append(model_dict)

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception:
            # If caching fails, continue without cache
            pass

    def clear_cache(self) -> None:
        """Clear all cached model data."""
        for cache_file in self.cache_dir.glob("models_*.json"):
            cache_file.unlink(missing_ok=True)


class OpenRouterModelFetcher:
    """Service for fetching and managing OpenRouter models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        cache: Optional[ModelCache] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ModelFetchError("OPENROUTER_API_KEY is required")

        self.base_url = base_url.rstrip('/')
        self.cache = cache or ModelCache()
        self.timeout = timeout

        # HTTP client configuration
        self.client_config = {
            "base_url": self.base_url,
            "timeout": httpx.Timeout(timeout),
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", ""),
                "X-Title": os.getenv("OPENROUTER_SITE_NAME", "OpenRouter Model Fetcher"),
            }
        }

    async def fetch_models(
        self,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> List[OpenRouterModel]:
        """Fetch all available models from OpenRouter API."""
        cache_key = "all_models"

        # Try cache first
        if use_cache and not force_refresh:
            cached_models = await self.cache.get_cached_models(cache_key)
            if cached_models:
                return cached_models

        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get("/models")
                response.raise_for_status()

                api_data = response.json()
                models = []

                for model_data in api_data.get("data", []):
                    try:
                        model = self._parse_api_model(model_data)
                        models.append(model)
                    except Exception as e:
                        # Continue parsing other models if one fails
                        continue

                # Cache the results
                if use_cache:
                    await self.cache.cache_models(models, cache_key)

                return models

        except httpx.HTTPStatusError as e:
            raise ModelFetchError(f"HTTP error fetching models: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ModelFetchError(f"Network error fetching models: {str(e)}")
        except Exception as e:
            raise ModelFetchError(f"Unexpected error fetching models: {str(e)}")

    async def get_model_details(self, model_id: str, use_cache: bool = True) -> Optional[OpenRouterModel]:
        """Get detailed information for a specific model."""
        models = await self.fetch_models(use_cache=use_cache)

        for model in models:
            if model.id == model_id:
                return model

        return None

    def _parse_api_model(self, model_data: Dict[str, Any]) -> OpenRouterModel:
        """Parse model data from OpenRouter API response."""
        # Extract basic information
        model_id = model_data.get("id", "")
        name = model_data.get("name", model_id)
        provider = model_data.get("provider", "")

        # Extract capabilities
        capabilities = set()
        api_capabilities = model_data.get("capabilities", {})
        for cap_name, enabled in api_capabilities.items():
            if enabled and cap_name in ModelCapability.__members__:
                capabilities.add(ModelCapability(cap_name))

        # Add basic capabilities that most models have
        if not capabilities:
            capabilities = {
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING
            }

        # Extract pricing information
        pricing_data = model_data.get("pricing", {})
        pricing = None
        if pricing_data:
            try:
                pricing = ModelPricing(
                    model_id=model_id,
                    input_cost_per_million=Decimal(str(pricing_data.get("prompt", "0"))),
                    output_cost_per_million=Decimal(str(pricing_data.get("completion", "0"))),
                    context_window=model_data.get("context_length"),
                    provider=provider
                )
            except Exception:
                pass  # Continue without pricing if parsing fails

        # Extract other information
        context_length = model_data.get("context_length")
        description = model_data.get("description")

        # Determine model size based on context length or name
        model_size = self._estimate_model_size(model_id, context_length)

        # Extract tags
        tags = set()
        if "tags" in model_data:
            tags = set(model_data["tags"])

        return OpenRouterModel(
            id=model_id,
            name=name,
            provider=provider,
            description=description,
            capabilities=capabilities,
            context_length=context_length,
            pricing=pricing,
            model_size=model_size,
            tags=tags,
            category=model_data.get("category"),
            is_open_source=model_data.get("is_open_source", False),
            architecture=model_data.get("architecture")
        )

    def _estimate_model_size(self, model_id: str, context_length: Optional[int]) -> Optional[ModelSize]:
        """Estimate model size based on model ID and context length."""
        model_id_lower = model_id.lower()

        # Check for explicit size indicators in name
        if any(size in model_id_lower for size in ["tiny", "small", "mini"]):
            return ModelSize.TINY
        elif any(size in model_id_lower for size in ["base", "1b", "2b", "3b"]):
            return ModelSize.SMALL
        elif any(size in model_id_lower for size in ["medium", "7b", "8b", "13b"]):
            return ModelSize.MEDIUM
        elif any(size in model_id_lower for size in ["large", "35b", "40b", "70b"]):
            return ModelSize.LARGE
        elif any(size in model_id_lower for size in ["xlarge", "100b", "180b", "405b"]):
            return ModelSize.XLARGE

        # Estimate based on context length
        if context_length:
            if context_length <= 4096:
                return ModelSize.SMALL
            elif context_length <= 8192:
                return ModelSize.MEDIUM
            elif context_length <= 32768:
                return ModelSize.LARGE
            else:
                return ModelSize.XLARGE

        return None


class ModelFilter:
    """Service for filtering and searching OpenRouter models."""

    def __init__(self, models: List[OpenRouterModel]):
        self.models = models

    def filter_by_provider(self, provider: Union[str, ProviderCategory]) -> List[OpenRouterModel]:
        """Filter models by provider or provider category."""
        if isinstance(provider, ProviderCategory):
            return [m for m in self.models if m.get_provider_category() == provider]
        else:
            provider_lower = provider.lower()
            return [m for m in self.models if provider_lower in m.provider.lower()]

    def filter_by_capability(self, capability: ModelCapability) -> List[OpenRouterModel]:
        """Filter models that support a specific capability."""
        return [m for m in self.models if m.supports_capability(capability)]

    def filter_by_capabilities(self, capabilities: Set[ModelCapability]) -> List[OpenRouterModel]:
        """Filter models that support all specified capabilities."""
        return [
            m for m in self.models
            if all(m.supports_capability(cap) for cap in capabilities)
        ]

    def filter_by_cost(
        self,
        max_input_cost: Optional[Decimal] = None,
        max_output_cost: Optional[Decimal] = None,
        cost_category: Optional[str] = None
    ) -> List[OpenRouterModel]:
        """Filter models by cost constraints."""
        filtered = []

        for model in self.models:
            if not model.pricing:
                continue

            # Filter by max input cost
            if max_input_cost and model.pricing.input_cost_per_million > max_input_cost:
                continue

            # Filter by max output cost
            if max_output_cost and model.pricing.output_cost_per_million > max_output_cost:
                continue

            # Filter by cost category
            if cost_category:
                if cost_category == "fast" and not model.is_fast_model():
                    continue
                elif cost_category == "premium" and not model.is_premium_model():
                    continue

            filtered.append(model)

        return filtered

    def filter_by_context_length(self, min_context: Optional[int] = None) -> List[OpenRouterModel]:
        """Filter models by minimum context length."""
        if min_context is None:
            return self.models

        return [
            m for m in self.models
            if m.context_length and m.context_length >= min_context
        ]

    def filter_by_size(self, size: ModelSize) -> List[OpenRouterModel]:
        """Filter models by size category."""
        return [m for m in self.models if m.model_size == size]

    def filter_by_availability(self, available: bool = True) -> List[OpenRouterModel]:
        """Filter models by availability status."""
        return [m for m in self.models if m.is_available == available]

    def filter_by_tags(self, tags: Union[str, Set[str]], match_all: bool = False) -> List[OpenRouterModel]:
        """Filter models by tags."""
        if isinstance(tags, str):
            tags = {tags}

        if match_all:
            return [m for m in self.models if tags.issubset(m.tags)]
        else:
            return [m for m in self.models if bool(tags.intersection(m.tags))]

    def search(self, query: str) -> List[OpenRouterModel]:
        """Search models by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for model in self.models:
            # Search in name
            if query_lower in model.name.lower():
                results.append(model)
                continue

            # Search in description
            if model.description and query_lower in model.description.lower():
                results.append(model)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in model.tags):
                results.append(model)
                continue

        return results

    def get_fastest_models(self, limit: int = 5) -> List[OpenRouterModel]:
        """Get the fastest (cheapest) models."""
        models_with_pricing = [m for m in self.models if m.pricing]
        sorted_models = sorted(models_with_pricing, key=lambda m: m.pricing.input_cost_per_million)
        return sorted_models[:limit]

    def get_most_capable_models(
        self,
        capabilities: Set[ModelCapability],
        limit: int = 5
    ) -> List[OpenRouterModel]:
        """Get models with the most capabilities."""
        capable_models = self.filter_by_capabilities(capabilities)

        # Sort by number of capabilities (descending)
        sorted_models = sorted(
            capable_models,
            key=lambda m: len(m.capabilities),
            reverse=True
        )
        return sorted_models[:limit]

    def group_by_provider(self) -> Dict[ProviderCategory, List[OpenRouterModel]]:
        """Group models by provider category."""
        groups = {}
        for model in self.models:
            category = model.get_provider_category()
            if category not in groups:
                groups[category] = []
            groups[category].append(model)
        return groups


# Convenience functions for common operations

async def get_all_models(
    api_key: Optional[str] = None,
    use_cache: bool = True,
    force_refresh: bool = False
) -> List[OpenRouterModel]:
    """Get all available OpenRouter models."""
    fetcher = OpenRouterModelFetcher(api_key=api_key)
    return await fetcher.fetch_models(use_cache=use_cache, force_refresh=force_refresh)


async def get_model_by_id(
    model_id: str,
    api_key: Optional[str] = None,
    use_cache: bool = True
) -> Optional[OpenRouterModel]:
    """Get a specific model by ID."""
    fetcher = OpenRouterModelFetcher(api_key=api_key)
    return await fetcher.get_model_details(model_id, use_cache=use_cache)


async def get_fast_models(
    limit: int = 10,
    max_cost_per_million: Decimal = Decimal('1.0'),
    api_key: Optional[str] = None,
    use_cache: bool = True
) -> List[OpenRouterModel]:
    """Get fast models within a cost limit."""
    models = await get_all_models(api_key=api_key, use_cache=use_cache)
    filter_service = ModelFilter(models)

    fast_models = filter_service.filter_by_cost(max_input_cost=max_cost_per_million)
    return filter_service.get_fastest_models(limit)


async def get_models_for_capability(
    capability: ModelCapability,
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_cost: Optional[Decimal] = None
) -> List[OpenRouterModel]:
    """Get models that support a specific capability."""
    models = await get_all_models(api_key=api_key, use_cache=use_cache)
    filter_service = ModelFilter(models)

    capable_models = filter_service.filter_by_capability(capability)

    if max_cost:
        capable_models = filter_service.filter_by_cost(max_input_cost=max_cost)

    return capable_models


async def get_code_generation_models(
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_cost: Optional[Decimal] = None
) -> List[OpenRouterModel]:
    """Get models suitable for code generation."""
    return await get_models_for_capability(
        ModelCapability.CODE_GENERATION,
        api_key=api_key,
        use_cache=use_cache,
        max_cost=max_cost
    )


async def get_vision_models(
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_cost: Optional[Decimal] = None
) -> List[OpenRouterModel]:
    """Get models with vision capabilities."""
    return await get_models_for_capability(
        ModelCapability.VISION,
        api_key=api_key,
        use_cache=use_cache,
        max_cost=max_cost
    )


async def get_function_calling_models(
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_cost: Optional[Decimal] = None
) -> List[OpenRouterModel]:
    """Get models that support function calling."""
    return await get_models_for_capability(
        ModelCapability.FUNCTION_CALLING,
        api_key=api_key,
        use_cache=use_cache,
        max_cost=max_cost
    )


# Export all public interfaces
__all__ = [
    # Core classes
    "OpenRouterModel",
    "ModelPricing",
    "OpenRouterModelFetcher",
    "ModelCache",
    "ModelFilter",

    # Enums
    "ModelCapability",
    "ProviderCategory",
    "ModelSize",

    # Exceptions
    "OpenRouterError",
    "ModelFetchError",
    "ModelValidationError",

    # Convenience functions
    "get_all_models",
    "get_model_by_id",
    "get_fast_models",
    "get_models_for_capability",
    "get_code_generation_models",
    "get_vision_models",
    "get_function_calling_models",
]