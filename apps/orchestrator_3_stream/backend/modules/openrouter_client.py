"""
Lightweight OpenRouter client for running OpenAI-compatible chat completions.

We only implement the bits we need for fast single-shot queries so we can
avoid the Anthropic CLI entirely when routing through OpenRouter.
"""

from __future__ import annotations

import os
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from openai import AsyncOpenAI, APIStatusError, APIConnectionError
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam, ChatCompletionChunk
from openai.types import CompletionUsage
from pydantic import BaseModel
from .logger import get_logger

logger = get_logger()


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter responds with an error."""


class OpenRouterMethodNotAllowedError(OpenRouterError):
    """Raised when OpenRouter responds with 405 Method Not Allowed."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class OpenRouterHTTPError(OpenRouterError):
    """HTTP-specific error with status code and details."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TokenCostCategory(str, Enum):
    """Token cost categories for different pricing tiers."""
    INPUT = "input"
    OUTPUT = "output"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"


@dataclass
class TokenCost:
    """Cost information for a specific token category."""
    category: TokenCostCategory
    tokens: int
    cost_usd: Decimal
    model_id: str
    timestamp: datetime


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""
    model_id: str
    input_cost_per_million: Decimal  # Cost per 1M input tokens
    output_cost_per_million: Decimal  # Cost per 1M output tokens
    cache_read_cost_per_million: Optional[Decimal] = None  # Cost per 1M cache read tokens
    cache_write_cost_per_million: Optional[Decimal] = None  # Cost per 1M cache write tokens
    context_window: Optional[int] = None  # Maximum context window size

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


class CostTrackingSession(BaseModel):
    """Tracks costs and usage for a series of OpenRouter requests."""
    session_id: str
    model_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    total_cost_usd: Decimal = Decimal('0')
    request_count: int = 0

    def add_usage(self, usage_data: 'UsageData') -> None:
        """Add usage data from a single request to the session."""
        self.total_input_tokens += usage_data.input_tokens
        self.total_output_tokens += usage_data.output_tokens
        self.total_cache_read_tokens += usage_data.cache_read_tokens
        self.total_cache_write_tokens += usage_data.cache_write_tokens
        self.total_cost_usd += usage_data.total_cost_usd
        self.request_count += 1

    def finish_session(self) -> None:
        """Mark the session as finished."""
        self.end_time = datetime.now(timezone.utc)


class UsageData(BaseModel):
    """Token usage and cost information for a single request."""
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: Decimal = Decimal('0')
    cached_tokens_percentage: Optional[float] = None
    timestamp: datetime
    request_id: Optional[str] = None

    @property
    def cost_breakdown(self) -> Dict[TokenCostCategory, Decimal]:
        """Get cost breakdown by category."""
        return {
            TokenCostCategory.INPUT: self.calculate_category_cost(TokenCostCategory.INPUT),
            TokenCostCategory.OUTPUT: self.calculate_category_cost(TokenCostCategory.OUTPUT),
            TokenCostCategory.CACHE_READ: self.calculate_category_cost(TokenCostCategory.CACHE_READ),
            TokenCostCategory.CACHE_WRITE: self.calculate_category_cost(TokenCostCategory.CACHE_WRITE),
        }

    def calculate_category_cost(self, category: TokenCostCategory) -> Decimal:
        """Calculate cost for a specific token category."""
        pricing = get_model_pricing(self.model_id)
        if not pricing:
            return Decimal('0')

        if category == TokenCostCategory.INPUT:
            return (Decimal(self.input_tokens) / Decimal('1000000')) * pricing.input_cost_per_million
        elif category == TokenCostCategory.OUTPUT:
            return (Decimal(self.output_tokens) / Decimal('1000000')) * pricing.output_cost_per_million
        elif category == TokenCostCategory.CACHE_READ:
            if self.cache_read_tokens > 0 and pricing.cache_read_cost_per_million:
                return (Decimal(self.cache_read_tokens) / Decimal('1000000')) * pricing.cache_read_cost_per_million
        elif category == TokenCostCategory.CACHE_WRITE:
            if self.cache_write_tokens > 0 and pricing.cache_write_cost_per_million:
                return (Decimal(self.cache_write_tokens) / Decimal('1000000')) * pricing.cache_write_cost_per_million

        return Decimal('0')


# OpenRouter Model Pricing Database
# Prices are in USD per 1M tokens as of 2024
OPENROUTER_PRICING_DB: Dict[str, ModelPricing] = {
    # Anthropic Models
    "anthropic/claude-3.5-sonnet": ModelPricing(
        model_id="anthropic/claude-3.5-sonnet",
        input_cost_per_million=Decimal('3.00'),
        output_cost_per_million=Decimal('15.00'),
        context_window=200000
    ),
    "anthropic/claude-3.5-haiku": ModelPricing(
        model_id="anthropic/claude-3.5-haiku",
        input_cost_per_million=Decimal('0.80'),
        output_cost_per_million=Decimal('4.00'),
        context_window=200000
    ),
    "anthropic/claude-3-opus": ModelPricing(
        model_id="anthropic/claude-3-opus",
        input_cost_per_million=Decimal('15.00'),
        output_cost_per_million=Decimal('75.00'),
        context_window=200000
    ),
    "anthropic/claude-3-sonnet": ModelPricing(
        model_id="anthropic/claude-3-sonnet",
        input_cost_per_million=Decimal('3.00'),
        output_cost_per_million=Decimal('15.00'),
        context_window=200000
    ),
    "anthropic/claude-3-haiku": ModelPricing(
        model_id="anthropic/claude-3-haiku",
        input_cost_per_million=Decimal('0.25'),
        output_cost_per_million=Decimal('1.25'),
        context_window=200000
    ),

    # OpenAI Models
    "openai/gpt-4o": ModelPricing(
        model_id="openai/gpt-4o",
        input_cost_per_million=Decimal('2.50'),
        output_cost_per_million=Decimal('10.00'),
        context_window=128000
    ),
    "openai/gpt-4o-mini": ModelPricing(
        model_id="openai/gpt-4o-mini",
        input_cost_per_million=Decimal('0.15'),
        output_cost_per_million=Decimal('0.60'),
        context_window=128000
    ),
    "openai/gpt-4-turbo": ModelPricing(
        model_id="openai/gpt-4-turbo",
        input_cost_per_million=Decimal('10.00'),
        output_cost_per_million=Decimal('30.00'),
        context_window=128000
    ),
    "openai/gpt-3.5-turbo": ModelPricing(
        model_id="openai/gpt-3.5-turbo",
        input_cost_per_million=Decimal('0.50'),
        output_cost_per_million=Decimal('1.50'),
        context_window=16385
    ),

    # Google Models
    "google/gemini-2.0-flash-exp": ModelPricing(
        model_id="google/gemini-2.0-flash-exp",
        input_cost_per_million=Decimal('0.075'),
        output_cost_per_million=Decimal('0.30'),
        context_window=1048576
    ),
    "google/gemini-1.5-pro": ModelPricing(
        model_id="google/gemini-1.5-pro",
        input_cost_per_million=Decimal('1.25'),
        output_cost_per_million=Decimal('5.00'),
        context_window=2097152
    ),
    "google/gemini-1.5-flash": ModelPricing(
        model_id="google/gemini-1.5-flash",
        input_cost_per_million=Decimal('0.075'),
        output_cost_per_million=Decimal('0.30'),
        context_window=1048576
    ),

    # Meta Models
    "meta-llama/llama-3.1-405b-instruct": ModelPricing(
        model_id="meta-llama/llama-3.1-405b-instruct",
        input_cost_per_million=Decimal('0.90'),
        output_cost_per_million=Decimal('2.40'),
        context_window=131072
    ),
    "meta-llama/llama-3.1-70b-instruct": ModelPricing(
        model_id="meta-llama/llama-3.1-70b-instruct",
        input_cost_per_million=Decimal('0.35'),
        output_cost_per_million=Decimal('1.00'),
        context_window=131072
    ),
    "meta-llama/llama-3.1-8b-instruct": ModelPricing(
        model_id="meta-llama/llama-3.1-8b-instruct",
        input_cost_per_million=Decimal('0.05'),
        output_cost_per_million=Decimal('0.10'),
        context_window=131072
    ),

    # xAI Models
    "x-ai/grok-2-1212": ModelPricing(
        model_id="x-ai/grok-2-1212",
        input_cost_per_million=Decimal('2.00'),
        output_cost_per_million=Decimal('10.00'),
        context_window=131072
    ),

    # Mistral Models
    "mistralai/mistral-large": ModelPricing(
        model_id="mistralai/mistral-large",
        input_cost_per_million=Decimal('2.00'),
        output_cost_per_million=Decimal('6.00'),
        context_window=32768
    ),
    "mistralai/mistral-medium": ModelPricing(
        model_id="mistralai/mistral-medium",
        input_cost_per_million=Decimal('2.70'),
        output_cost_per_million=Decimal('8.10'),
        context_window=32768
    ),
    "mistralai/mistral-small": ModelPricing(
        model_id="mistralai/mistral-small",
        input_cost_per_million=Decimal('0.20'),
        output_cost_per_million=Decimal('0.60'),
        context_window=32768
    ),

    # Other Models
    "cohere/command-r-plus": ModelPricing(
        model_id="cohere/command-r-plus",
        input_cost_per_million=Decimal('3.00'),
        output_cost_per_million=Decimal('15.00'),
        context_window=128000
    ),
    "cohere/command-r": ModelPricing(
        model_id="cohere/command-r",
        input_cost_per_million=Decimal('0.50'),
        output_cost_per_million=Decimal('1.50'),
        context_window=128000
    ),
    "perplexity/llama-3.1-sonar-large-128k-online": ModelPricing(
        model_id="perplexity/llama-3.1-sonar-large-128k-online",
        input_cost_per_million=Decimal('1.00'),
        output_cost_per_million=Decimal('1.00'),
        context_window=127072
    ),
    "perplexity/llama-3.1-sonar-small-128k-online": ModelPricing(
        model_id="perplexity/llama-3.1-sonar-small-128k-online",
        input_cost_per_million=Decimal('0.20'),
        output_cost_per_million=Decimal('0.20'),
        context_window=127072
    ),
}

# Global cost tracking session
_active_sessions: Dict[str, CostTrackingSession] = {}


_CLIENT: AsyncOpenAI | None = None


def _log_request_details(method: str, url: str, headers: dict, data: dict = None):
    """Log detailed request information for debugging."""
    logger.info(f"OpenRouter Request: {method} {url}")
    logger.debug(f"Headers: {headers}")
    if data:
        logger.debug(f"Request data keys: {list(data.keys())}")


def _get_endpoint_url(base_url: str, endpoint: str) -> str:
    """Get endpoint URL without double slashes."""
    # Remove leading slash from endpoint if base_url ends with slash
    if endpoint.startswith('/') and base_url.endswith('/'):
        endpoint = endpoint[1:]
    return f"{base_url}{endpoint}"


def _get_client() -> AsyncOpenAI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # VALIDATE URL FORMAT
    original_base_url = base_url
    if not base_url.endswith('/v1'):
        logger.warning(f"OpenRouter base URL should end with /v1: {base_url}")
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        base_url = base_url + 'v1'

    # Don't remove trailing slash here - let OpenAI client handle it
    # Just ensure we don't have double /v1
    if '/v1/v1' in base_url:
        base_url = base_url.replace('/v1/v1', '/v1')

    logger.info(f"OpenRouter client configured with base URL: {base_url}")

    headers: Dict[str, str] = {}
    site_url = os.getenv("OPENROUTER_SITE_URL")
    site_name = os.getenv("OPENROUTER_SITE_NAME")
    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-Title"] = site_name

    _CLIENT = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        default_headers=headers or None,
    )
    return _CLIENT


async def create_completion(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> ChatCompletion:
    """Execute a standard (non-streaming) chat completion call."""
    client = _get_client()

    # Log request details for debugging
    _log_request_details(
        method="POST",
        url=_get_endpoint_url(str(client.base_url), "/chat/completions"),
        headers=client.default_headers or {},
        data={"model": model, "message_count": len(messages)}
    )

    try:
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False,
            max_tokens=max_tokens,
        )
    except APIStatusError as exc:
        # Handle specific HTTP status codes
        if exc.status_code == 405:
            logger.error("=== OPENROUTER 405 ERROR DIAGNOSTICS ===")
            logger.error(f"Base URL: {client.base_url}")
            correct_url = _get_endpoint_url(str(client.base_url), "/chat/completions")
            logger.error(f"Full Request URL: {correct_url}")
            logger.error(f"HTTP Method: POST")
            logger.error(f"Request Headers: {client.default_headers}")
            api_key = os.getenv("OPENROUTER_API_KEY")
            logger.error(f"API Key Present: {bool(api_key)}")
            logger.error(f"API Key Prefix: {api_key[:8] + '...' if api_key else 'None'}")
            if hasattr(exc, 'response') and exc.response:
                logger.error(f"Response Headers: {dict(exc.response.headers)}")
                logger.error(f"Response Body: {exc.response.text}")
            logger.error("=== END DIAGNOSTICS ===")
            raise OpenRouterMethodNotAllowedError(
                message=f"HTTP 405 Method Not Allowed from OpenRouter",
                details={
                    "base_url": str(client.base_url),
                    "request_url": _get_endpoint_url(str(client.base_url), "/chat/completions"),
                    "method": "POST",
                    "response_headers": dict(exc.response.headers) if exc.response else {},
                    "response_body": exc.response.text if exc.response else None
                }
            ) from exc
        else:
            logger.error(f"OpenRouter API error {exc.status_code}: {exc.message}")
            raise OpenRouterHTTPError(
                f"OpenRouter API error {exc.status_code}: {exc.message}",
                status_code=exc.status_code,
                response=getattr(exc, 'response', None)
            ) from exc
    except APIConnectionError as exc:
        logger.error(f"OpenRouter connection error: {exc}")
        raise OpenRouterError(f"OpenRouter connection failed: {exc}") from exc
    except Exception as exc:
        logger.error(f"OpenRouter unexpected error: {exc}")
        raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc


def extract_text(completion: ChatCompletion) -> str:
    """Extract text content from the first choice."""
    if not completion.choices:
        raise OpenRouterError("OpenRouter response missing choices")
    content = completion.choices[0].message.content
    if isinstance(content, list):
        text = "".join(
            chunk.get("text", "")
            for chunk in content
            if isinstance(chunk, dict)
        )
    elif isinstance(content, str):
        text = content
    else:
        raise OpenRouterError("Unsupported OpenRouter response format")
    return text.strip()


async def complete_text(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Execute a single OpenRouter chat completion call (system + user prompt) and return text.
    """
    messages: List[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    completion = await create_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return extract_text(completion)


async def create_completion_stream(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[ChatCompletionChunk, None]:
    """Execute a streaming chat completion call."""
    client = _get_client()

    # Log request details for debugging
    _log_request_details(
        method="POST",
        url=_get_endpoint_url(str(client.base_url), "/chat/completions"),
        headers=client.default_headers or {},
        data={"model": model, "message_count": len(messages), "stream": True}
    )

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            max_tokens=max_tokens,
        )
        async for chunk in stream:
            yield chunk
    except APIStatusError as exc:
        # Handle specific HTTP status codes
        if exc.status_code == 405:
            logger.error("=== OPENROUTER 405 ERROR DIAGNOSTICS (STREAMING) ===")
            logger.error(f"Base URL: {client.base_url}")
            correct_url = _get_endpoint_url(str(client.base_url), "/chat/completions")
            logger.error(f"Full Request URL: {correct_url}")
            logger.error(f"HTTP Method: POST")
            logger.error(f"Request Headers: {client.default_headers}")
            api_key = os.getenv("OPENROUTER_API_KEY")
            logger.error(f"API Key Present: {bool(api_key)}")
            logger.error(f"API Key Prefix: {api_key[:8] + '...' if api_key else 'None'}")
            if hasattr(exc, 'response') and exc.response:
                logger.error(f"Response Headers: {dict(exc.response.headers)}")
                logger.error(f"Response Body: {exc.response.text}")
            logger.error("=== END DIAGNOSTICS ===")
            raise OpenRouterMethodNotAllowedError(
                message=f"HTTP 405 Method Not Allowed from OpenRouter (streaming)",
                details={
                    "base_url": str(client.base_url),
                    "request_url": _get_endpoint_url(str(client.base_url), "/chat/completions"),
                    "method": "POST",
                    "response_headers": dict(exc.response.headers) if exc.response else {},
                    "response_body": exc.response.text if exc.response else None,
                    "streaming": True
                }
            ) from exc
        else:
            logger.error(f"OpenRouter API streaming error {exc.status_code}: {exc.message}")
            raise OpenRouterHTTPError(
                f"OpenRouter API streaming error {exc.status_code}: {exc.message}",
                status_code=exc.status_code,
                response=getattr(exc, 'response', None)
            ) from exc
    except APIConnectionError as exc:
        logger.error(f"OpenRouter streaming connection error: {exc}")
        raise OpenRouterError(f"OpenRouter streaming connection failed: {exc}") from exc
    except Exception as exc:
        logger.error(f"OpenRouter streaming unexpected error: {exc}")
        raise OpenRouterError(f"OpenRouter streaming request failed: {exc}") from exc


async def complete_text_stream(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """
    Execute a single OpenRouter streaming chat completion call (system + user prompt) and yield text chunks.
    """
    messages: List[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async for chunk in create_completion_stream(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# Cost Tracking Functions

def get_model_pricing(model_id: str) -> Optional[ModelPricing]:
    """Get pricing information for a specific model."""
    return OPENROUTER_PRICING_DB.get(model_id)


def list_available_models() -> List[str]:
    """Get list of all available models with pricing information."""
    return list(OPENROUTER_PRICING_DB.keys())


def create_cost_tracking_session(session_id: str, model_id: str) -> CostTrackingSession:
    """Create a new cost tracking session."""
    session = CostTrackingSession(
        session_id=session_id,
        model_id=model_id,
        start_time=datetime.now(timezone.utc)
    )
    _active_sessions[session_id] = session
    return session


def get_cost_tracking_session(session_id: str) -> Optional[CostTrackingSession]:
    """Get an existing cost tracking session."""
    return _active_sessions.get(session_id)


def finish_cost_tracking_session(session_id: str) -> Optional[CostTrackingSession]:
    """Finish a cost tracking session and return the final session data."""
    session = _active_sessions.get(session_id)
    if session:
        session.finish_session()
        # Remove from active sessions but return the completed session
        del _active_sessions[session_id]
    return session


def extract_usage_from_completion(completion: ChatCompletion, model_id: str) -> UsageData:
    """Extract usage information from a non-streaming completion response."""
    # Extract usage data from OpenAI completion
    usage = completion.usage
    input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

    # Check for OpenRouter-specific cost information
    total_cost_usd = Decimal('0')

    # Try to extract cost from completion response
    if hasattr(completion, 'model_extra') and completion.model_extra:
        cost_info = completion.model_extra.get('cost', {})
        if cost_info:
            total_cost_usd = Decimal(str(cost_info.get('amount', 0)))

    # If no cost info, calculate based on pricing
    if total_cost_usd == Decimal('0'):
        pricing = get_model_pricing(model_id)
        if pricing:
            total_cost_usd = pricing.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

    return UsageData(
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        total_cost_usd=total_cost_usd,
        timestamp=datetime.now(timezone.utc),
        request_id=getattr(completion, 'id', None)
    )


class StreamingUsageAccumulator:
    """Accumulates usage data across streaming completion chunks."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.request_id: Optional[str] = None
        self.start_time = datetime.now(timezone.utc)

    def process_chunk(self, chunk: ChatCompletionChunk) -> None:
        """Process a streaming chunk and accumulate usage data."""
        usage = chunk.usage
        if usage:
            self.input_tokens += getattr(usage, "prompt_tokens", 0)
            self.output_tokens += getattr(usage, "completion_tokens", 0)
            self.total_tokens += getattr(usage, "total_tokens", 0)

            # Handle cache usage if available
            if hasattr(usage, "cache_creation_input_tokens"):
                self.cache_write_tokens += getattr(usage, "cache_creation_input_tokens", 0)
            if hasattr(usage, "cache_read_input_tokens"):
                self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0)

        # Store request ID from first chunk
        if not self.request_id and hasattr(chunk, 'id'):
            self.request_id = chunk.id

    def finalize(self) -> UsageData:
        """Finalize the usage data after streaming is complete."""
        # Calculate cost based on accumulated usage
        pricing = get_model_pricing(self.model_id)
        total_cost_usd = Decimal('0')

        if pricing:
            total_cost_usd = pricing.calculate_cost(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
                cache_read_tokens=self.cache_read_tokens,
                cache_write_tokens=self.cache_write_tokens
            )

        # Calculate cached tokens percentage if applicable
        cached_percentage = None
        total_cache_tokens = self.cache_read_tokens + self.cache_write_tokens
        if total_cache_tokens > 0:
            cached_percentage = (total_cache_tokens / max(self.input_tokens, 1)) * 100

        return UsageData(
            model_id=self.model_id,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_read_tokens=self.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens,
            total_tokens=self.total_tokens,
            total_cost_usd=total_cost_usd,
            cached_tokens_percentage=cached_percentage,
            timestamp=self.start_time,
            request_id=self.request_id
        )


async def create_completion_with_usage(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    session_id: Optional[str] = None
) -> tuple[ChatCompletion, UsageData]:
    """
    Execute a standard (non-streaming) chat completion call and return both completion and usage data.
    """
    completion = await create_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    usage_data = extract_usage_from_completion(completion, model)

    # Update session if provided
    if session_id:
        session = get_cost_tracking_session(session_id)
        if session:
            session.add_usage(usage_data)

    return completion, usage_data


async def create_completion_stream_with_usage(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    session_id: Optional[str] = None
) -> tuple[AsyncGenerator[ChatCompletionChunk, None], StreamingUsageAccumulator]:
    """
    Execute a streaming chat completion call and return both stream and usage accumulator.
    """
    accumulator = StreamingUsageAccumulator(model)

    async def stream_with_tracking():
        stream = await create_completion_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        async for chunk in stream:
            accumulator.process_chunk(chunk)
            yield chunk

        # Finalize usage after streaming is complete
        usage_data = accumulator.finalize()

        # Update session if provided
        if session_id:
            session = get_cost_tracking_session(session_id)
            if session:
                session.add_usage(usage_data)

    return stream_with_tracking(), accumulator


def format_cost_summary(usage_data: UsageData) -> str:
    """Format usage data into a human-readable cost summary."""
    lines = [
        f"Model: {usage_data.model_id}",
        f"Input Tokens: {usage_data.input_tokens:,}",
        f"Output Tokens: {usage_data.output_tokens:,}",
        f"Total Tokens: {usage_data.total_tokens:,}",
    ]

    if usage_data.cache_read_tokens > 0 or usage_data.cache_write_tokens > 0:
        lines.extend([
            f"Cache Read Tokens: {usage_data.cache_read_tokens:,}",
            f"Cache Write Tokens: {usage_data.cache_write_tokens:,}",
        ])
        if usage_data.cached_tokens_percentage:
            lines.append(f"Cache Hit Rate: {usage_data.cached_tokens_percentage:.1f}%")

    lines.append(f"Total Cost: ${float(usage_data.total_cost_usd):.6f}")

    # Add cost breakdown
    breakdown = usage_data.cost_breakdown
    if any(breakdown.values()):
        lines.append("\nCost Breakdown:")
        for category, cost in breakdown.items():
            if cost > 0:
                lines.append(f"  {category.value.title()}: ${float(cost):.6f}")

    return "\n".join(lines)


def format_session_summary(session: CostTrackingSession) -> str:
    """Format a cost tracking session into a human-readable summary."""
    duration = (session.end_time or datetime.now(timezone.utc)) - session.start_time

    lines = [
        f"Session ID: {session.session_id}",
        f"Model: {session.model_id}",
        f"Requests: {session.request_count}",
        f"Duration: {duration.total_seconds():.1f} seconds",
        "",
        "Total Usage:",
        f"  Input Tokens: {session.total_input_tokens:,}",
        f"  Output Tokens: {session.total_output_tokens:,}",
    ]

    if session.total_cache_read_tokens > 0 or session.total_cache_write_tokens > 0:
        lines.extend([
            f"  Cache Read Tokens: {session.total_cache_read_tokens:,}",
            f"  Cache Write Tokens: {session.total_cache_write_tokens:,}",
        ])

    lines.extend([
        "",
        f"Total Cost: ${float(session.total_cost_usd):.6f}",
        f"Average Cost per Request: ${float(session.total_cost_usd / max(session.request_count, 1)):.6f}",
    ])

    return "\n".join(lines)


def estimate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0
) -> Optional[Decimal]:
    """Estimate cost for a request before making it."""
    pricing = get_model_pricing(model_id)
    if not pricing:
        return None

    return pricing.calculate_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens
    )


def get_model_context_window(model_id: str) -> Optional[int]:
    """Get the context window size for a model."""
    pricing = get_model_pricing(model_id)
    return pricing.context_window if pricing else None


def calculate_context_usage_percentage(model_id: str, input_tokens: int) -> Optional[float]:
    """Calculate context usage percentage for a given model and input tokens."""
    context_window = get_model_context_window(model_id)
    if not context_window:
        return None

    return (input_tokens / context_window) * 100


async def _validate_openrouter_endpoints() -> bool:
    """Validate that OpenRouter endpoints accept correct HTTP methods."""
    try:
        import httpx
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        if not api_key:
            logger.warning("Cannot validate OpenRouter endpoints: OPENROUTER_API_KEY not set")
            return False

        async with httpx.AsyncClient(timeout=10.0) as http_client:
            # Test chat completions endpoint with OPTIONS request
            response = await http_client.options(
                _get_endpoint_url(base_url.rstrip('/'), "/chat/completions"),
                headers={"Authorization": f"Bearer {api_key}"}
            )
            logger.info(f"OpenRouter OPTIONS /chat/completions: {response.status_code}")
            logger.info(f"Allowed methods: {response.headers.get('Allow', 'Not specified')}")
            return response.status_code in [200, 405]  # 405 is acceptable for OPTIONS
    except Exception as exc:
        logger.warning(f"Could not validate OpenRouter endpoints: {exc}")
        return False


def _get_client_diagnostics() -> dict:
    """Get diagnostic information about OpenRouter client configuration."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    return {
        "api_key_set": bool(api_key),
        "api_key_prefix": api_key[:8] + "..." if api_key else None,
        "base_url": base_url,
        "client_type": "openai.AsyncOpenAI",
        "expected_methods": {
            "chat_completions": "POST",
            "models": "GET",
            "pricing": "GET"
        }
    }


async def create_completion_with_fallback(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> ChatCompletion:
    """Execute chat completion with fallback mechanisms."""

    # Try standard approach first
    try:
        return await create_completion(messages, model, temperature, max_tokens)
    except OpenRouterMethodNotAllowedError as exc:
        logger.warning(f"Standard approach failed with 405, trying alternative configuration")

        # Alternative 1: Try with different base URL format
        try:
            # FIX DOUBLE /v1 ISSUE
            alt_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip('/')
            # Don't add /v1 if it's already there
            if not alt_base_url.endswith('/v1'):
                alt_base_url = alt_base_url + '/v1'

            client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=alt_base_url,
            )

            return await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False,
                max_tokens=max_tokens,
            )
        except Exception as fallback_exc:
            logger.error(f"Alternative configuration also failed: {fallback_exc}")

        # Alternative 2: Try direct HTTP request
        try:
            return await _direct_http_completion(messages, model, temperature, max_tokens)
        except Exception as direct_exc:
            logger.error(f"Direct HTTP request also failed: {direct_exc}")

        # All attempts failed
        raise OpenRouterError(
            f"All OpenRouter connection methods failed. "
            f"Original error: {exc}. "
            f"Please check your OpenRouter API key and configuration."
        )


async def _direct_http_completion(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> ChatCompletion:
    """Direct HTTP request to OpenRouter API as fallback."""
    import httpx
    import json

    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set for direct HTTP request")

    request_data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", ""),
        "X-Title": os.getenv("OPENROUTER_SITE_NAME", "")
    }

    logger.info(f"Attempting direct HTTP request to {base_url}/chat/completions")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            json=request_data,
            headers=headers,
        )

        if response.status_code == 405:
            raise OpenRouterMethodNotAllowedError(
                f"Direct HTTP request also returned 405. "
                f"Response: {response.text}"
            )
        elif response.status_code != 200:
            raise OpenRouterError(
                f"Direct HTTP request failed with {response.status_code}: {response.text}"
            )

        # Convert response back to OpenAI format
        return ChatCompletion.parse_raw(response.text)


__all__ = [
    # Core client functions
    "create_completion",
    "extract_text",
    "complete_text",
    "create_completion_stream",
    "complete_text_stream",

    # Enhanced functions with cost tracking
    "create_completion_with_usage",
    "create_completion_stream_with_usage",

    # Cost tracking data structures
    "TokenCostCategory",
    "TokenCost",
    "ModelPricing",
    "UsageData",
    "CostTrackingSession",
    "StreamingUsageAccumulator",

    # Cost tracking functions
    "get_model_pricing",
    "list_available_models",
    "create_cost_tracking_session",
    "get_cost_tracking_session",
    "finish_cost_tracking_session",
    "extract_usage_from_completion",

    # Utility functions
    "format_cost_summary",
    "format_session_summary",
    "estimate_cost",
    "get_model_context_window",
    "calculate_context_usage_percentage",

    # Pricing database
    "OPENROUTER_PRICING_DB",

    # Exception classes
    "OpenRouterError",
    "OpenRouterMethodNotAllowedError",
    "OpenRouterHTTPError",

    # Diagnostic functions
    "_validate_openrouter_endpoints",
    "_get_client_diagnostics",

    # Fallback functions
    "create_completion_with_fallback",
    "_direct_http_completion"
]
