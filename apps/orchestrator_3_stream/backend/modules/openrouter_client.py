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

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam, ChatCompletionChunk
from openai.types import CompletionUsage
from pydantic import BaseModel


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter responds with an error."""


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


def _get_client() -> AsyncOpenAI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set")

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

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
    try:
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
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

    # Exception class
    "OpenRouterError"
]
