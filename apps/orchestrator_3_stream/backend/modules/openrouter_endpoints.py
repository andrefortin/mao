"""
OpenRouter Provider Configuration API Endpoints

Comprehensive API endpoints for managing OpenRouter provider configurations,
including CRUD operations, model listing, cost estimation, and health checks.

Follows existing FastAPI patterns and Pydantic validation conventions.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from pydantic import BaseModel, Field, validator

from .openrouter_client import (
    OPENROUTER_PRICING_DB,
    ModelPricing,
    estimate_cost,
    get_model_context_window,
    calculate_context_usage_percentage,
    list_available_models,
    get_model_pricing,
    OpenRouterError
)
from . import database
from .logger import get_logger

logger = get_logger()


# ═══════════════════════════════════════════════════════════
# Pydantic Request/Response Models
# ═══════════════════════════════════════════════════════════


class OpenRouterProviderCreate(BaseModel):
    """Request model for creating OpenRouter provider configuration."""

    display_name: str = Field(..., description="Display name for the provider")
    provider_description: Optional[str] = Field(None, description="Description of the provider")
    api_key_encrypted: Optional[str] = Field(None, description="Encrypted API key")
    api_base_url: str = Field("https://openrouter.ai/api/v1", description="Base URL for OpenRouter API")
    site_url: Optional[str] = Field(None, description="Site URL for OpenRouter requests")
    site_name: Optional[str] = Field(None, description="Site name for OpenRouter requests")
    rate_limit_rpm: int = Field(60, description="Rate limit requests per minute")
    rate_limit_tpm: int = Field(10000, description="Rate limit tokens per minute")
    connection_timeout_seconds: int = Field(30, description="Connection timeout in seconds")
    read_timeout_seconds: int = Field(60, description="Read timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(1, description="Delay between retries in seconds")
    health_check_enabled: bool = Field(True, description="Enable health checks")
    health_check_interval_seconds: int = Field(300, description="Health check interval in seconds")
    is_default_provider: bool = Field(False, description="Set as default provider")
    priority_rank: int = Field(100, description="Priority rank for provider selection")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OpenRouterProviderUpdate(BaseModel):
    """Request model for updating OpenRouter provider configuration."""

    display_name: Optional[str] = Field(None, description="Display name for the provider")
    provider_description: Optional[str] = Field(None, description="Description of the provider")
    api_key_encrypted: Optional[str] = Field(None, description="Encrypted API key")
    api_base_url: Optional[str] = Field(None, description="Base URL for OpenRouter API")
    site_url: Optional[str] = Field(None, description="Site URL for OpenRouter requests")
    site_name: Optional[str] = Field(None, description="Site name for OpenRouter requests")
    rate_limit_rpm: Optional[int] = Field(None, description="Rate limit requests per minute")
    rate_limit_tpm: Optional[int] = Field(None, description="Rate limit tokens per minute")
    connection_timeout_seconds: Optional[int] = Field(None, description="Connection timeout in seconds")
    read_timeout_seconds: Optional[int] = Field(None, description="Read timeout in seconds")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts")
    retry_delay_seconds: Optional[int] = Field(None, description="Delay between retries in seconds")
    health_check_enabled: Optional[bool] = Field(None, description="Enable health checks")
    health_check_interval_seconds: Optional[int] = Field(None, description="Health check interval in seconds")
    is_default_provider: Optional[bool] = Field(None, description="Set as default provider")
    priority_rank: Optional[int] = Field(None, description="Priority rank for provider selection")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: Optional[str] = Field(None, description="Provider status")


class OpenRouterProviderResponse(BaseModel):
    """Response model for OpenRouter provider configuration."""

    id: str
    orchestrator_agent_id: str
    provider_name: str
    provider_type: str
    display_name: str
    api_base_url: str
    provider_description: Optional[str]
    provider_website: Optional[str]
    documentation_url: Optional[str]
    status: str
    rate_limit_rpm: int
    rate_limit_tpm: int
    rate_limit_tpd: int
    rate_limit_strategy: str
    connection_timeout_seconds: int
    read_timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    backoff_multiplier: float
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_audio: bool
    supports_embeddings: bool
    supports_fine_tuning: bool
    default_model_id: Optional[str]
    preferred_models: List[str]
    excluded_models: List[str]
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    last_request_at: Optional[datetime]
    last_error_at: Optional[datetime]
    last_error_message: Optional[str]
    consecutive_errors: int
    health_check_enabled: bool
    health_check_interval_seconds: int
    last_health_check_at: Optional[datetime]
    health_status: str
    health_check_endpoint: Optional[str]
    uptime_percentage: float
    is_default_provider: bool
    is_fallback_provider: bool
    priority_rank: int
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime]


class OpenRouterModelResponse(BaseModel):
    """Response model for OpenRouter model information."""

    id: str
    llm_provider_config_id: str
    model_id: str
    model_name: str
    provider_name: str
    model_family: Optional[str]
    context_length: Optional[int]
    max_output_tokens: Optional[int]
    input_token_limit: Optional[int]
    architecture: Optional[str]
    model_size: Optional[str]
    parameter_count: Optional[int]
    training_data_cutoff: Optional[datetime]
    is_open_source: bool
    capabilities: List[str]
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_audio: bool
    supports_json_mode: bool
    supports_image_generation: bool
    supports_embeddings: bool
    input_cost_per_million: float
    output_cost_per_million: float
    cache_read_cost_per_million: Optional[float]
    cache_write_cost_per_million: Optional[float]
    pricing_currency: str
    category: Optional[str]
    subcategory: Optional[str]
    tags: List[str]
    benchmark_scores: Dict[str, Any]
    latency_ms_average: Optional[float]
    throughput_tokens_per_second: Optional[float]
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    is_available: bool
    availability_status: Optional[str]
    deprecated_at: Optional[datetime]
    sunset_at: Optional[datetime]
    average_rating: Optional[float]
    review_count: int
    quality_score: Optional[float]
    available_regions: List[str]
    restricted_regions: List[str]
    requires_special_header: bool
    special_headers: Dict[str, Any]
    minimum_context_length: Optional[int]
    recommended_context_length: Optional[int]
    provider_model_url: Optional[str]
    documentation_url: Optional[str]
    model_card_url: Optional[str]
    is_recommended_model: bool
    is_popular_model: bool
    is_new_model: bool
    release_date: Optional[datetime]
    last_updated_by_provider: Optional[datetime]
    notes: Optional[str]
    internal_tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    last_pricing_update: Optional[datetime]


class CostEstimationRequest(BaseModel):
    """Request model for cost estimation."""

    model_id: str = Field(..., description="OpenRouter model ID")
    input_tokens: int = Field(..., ge=0, description="Number of input tokens")
    output_tokens: int = Field(..., ge=0, description="Number of output tokens")
    cache_read_tokens: int = Field(0, ge=0, description="Number of cache read tokens")
    cache_write_tokens: int = Field(0, ge=0, description="Number of cache write tokens")


class CostEstimationResponse(BaseModel):
    """Response model for cost estimation."""

    model_id: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    estimated_cost_usd: Optional[float]
    context_window: Optional[int]
    context_usage_percentage: Optional[float]
    pricing_info: Optional[Dict[str, Any]]


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    provider_id: str
    provider_name: str
    status: str
    is_healthy: bool
    response_time_ms: Optional[float]
    error_message: Optional[str]
    checked_at: datetime
    uptime_percentage: float
    consecutive_errors: int
    last_error_at: Optional[datetime]
    last_request_at: Optional[datetime]


class ModelListResponse(BaseModel):
    """Response model for model listing."""

    models: List[Dict[str, Any]]
    total_count: int
    provider_count: int
    last_updated: datetime


class ProviderStatsResponse(BaseModel):
    """Response model for provider statistics."""

    provider_id: str
    provider_name: str
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    average_cost_per_request: float
    average_tokens_per_request: float
    uptime_percentage: float
    error_rate: float
    last_request_at: Optional[datetime]
    most_used_models: List[Dict[str, Any]]
    cost_breakdown: Dict[str, float]


# ═══════════════════════════════════════════════════════════
# Database Helper Functions
# ═══════════════════════════════════════════════════════════


async def get_orchestrator_id() -> uuid.UUID:
    """Get the current orchestrator agent ID."""
    # This should be injected from the app state or passed as a dependency
    # For now, we'll assume there's a way to get it from the current context
    from .main import app
    orchestrator = app.state.orchestrator
    return orchestrator.id


async def provider_exists(provider_name: str) -> bool:
    """Check if a provider already exists."""
    orchestrator_id = await get_orchestrator_id()

    async with database.get_connection() as conn:
        result = await conn.fetchval(
            "SELECT id FROM llm_provider_configs WHERE orchestrator_agent_id = $1 AND provider_name = $2",
            orchestrator_id, provider_name
        )
        return result is not None


async def get_provider_config(provider_id: str) -> Optional[Dict[str, Any]]:
    """Get provider configuration by ID."""
    # For now, return a mock configuration
    # In a real implementation, this would query the database
    try:
        uuid.UUID(provider_id)  # Validate UUID format
    except ValueError:
        return None

    return {
        "id": provider_id,
        "provider_name": "openrouter",
        "provider_type": "openrouter",
        "display_name": "OpenRouter Provider",
        "api_base_url": "https://openrouter.ai/api/v1",
        "provider_description": "Multi-provider LLM access via OpenRouter",
        "provider_website": "https://openrouter.ai",
        "documentation_url": "https://openrouter.ai/docs",
        "status": "active",
        "health_check_enabled": True,
        "total_requests": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "uptime_percentage": 100.0,
        "consecutive_errors": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "custom_headers": {},
        "is_default_provider": False,
        "tags": ["openrouter", "multi-provider"],
        "metadata": {}
    }


async def create_provider_config(config_data: OpenRouterProviderCreate) -> Dict[str, Any]:
    """Create a new OpenRouter provider configuration."""
    # Generate a new provider ID
    provider_id = str(uuid.uuid4())

    # Create custom headers for OpenRouter
    custom_headers = {}
    if config_data.site_url:
        custom_headers["HTTP-Referer"] = config_data.site_url
    if config_data.site_name:
        custom_headers["X-Title"] = config_data.site_name

    # Return mock configuration (in real implementation, this would be saved to database)
    return {
        "id": provider_id,
        "provider_name": "openrouter",
        "provider_type": "openrouter",
        "display_name": config_data.display_name,
        "api_base_url": config_data.api_base_url,
        "api_key_encrypted": config_data.api_key_encrypted,
        "provider_description": config_data.provider_description,
        "provider_website": "https://openrouter.ai",
        "documentation_url": "https://openrouter.ai/docs",
        "status": "active",
        "rate_limit_rpm": config_data.rate_limit_rpm,
        "rate_limit_tpm": config_data.rate_limit_tpm,
        "rate_limit_tpd": 100000,
        "rate_limit_strategy": "sliding_window",
        "connection_timeout_seconds": config_data.connection_timeout_seconds,
        "read_timeout_seconds": config_data.read_timeout_seconds,
        "max_retries": config_data.max_retries,
        "retry_delay_seconds": config_data.retry_delay_seconds,
        "backoff_multiplier": 2.0,
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_audio": False,
        "supports_embeddings": False,
        "supports_fine_tuning": False,
        "preferred_models": [],
        "excluded_models": [],
        "custom_headers": custom_headers,
        "default_parameters": {},
        "total_requests": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "health_check_enabled": config_data.health_check_enabled,
        "health_check_interval_seconds": config_data.health_check_interval_seconds,
        "is_default_provider": config_data.is_default_provider,
        "is_fallback_provider": False,
        "priority_rank": config_data.priority_rank,
        "tags": config_data.tags,
        "metadata": config_data.metadata,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


async def update_provider_config(provider_id: str, update_data: OpenRouterProviderUpdate) -> Optional[Dict[str, Any]]:
    """Update an existing OpenRouter provider configuration."""
    config = await get_provider_config(provider_id)
    if not config:
        return None

    # Update the mock configuration with new values
    update_dict = update_data.dict(exclude_unset=True)
    config.update(update_dict)
    config["updated_at"] = datetime.now(timezone.utc)

    return config


async def delete_provider_config(provider_id: str) -> bool:
    """Soft delete a provider configuration."""
    config = await get_provider_config(provider_id)
    if not config:
        return False

    orchestrator_id = await get_orchestrator_id()

    async with database.get_connection() as conn:
        result = await conn.execute(
            """
            UPDATE llm_provider_configs
            SET archived = true, updated_at = NOW()
            WHERE id = $1 AND orchestrator_agent_id = $2
            """,
            uuid.UUID(provider_id), orchestrator_id
        )

    return result == "UPDATE 1"


async def list_provider_configs() -> List[Dict[str, Any]]:
    """List all provider configurations for the current orchestrator."""
    # Return mock list for now
    return [
        {
            "id": str(uuid.uuid4()),
            "provider_name": "openrouter",
            "provider_type": "openrouter",
            "display_name": "Default OpenRouter Provider",
            "status": "active",
            "is_default_provider": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]


async def sync_openrouter_models(provider_id: str) -> int:
    """Sync OpenRouter models from the pricing database."""
    config = await get_provider_config(provider_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider configuration not found"
        )

    provider_uuid = uuid.UUID(provider_id)
    models_synced = 0

    async with database.get_connection() as conn:
        # Clear existing models for this provider
        await conn.execute(
            "DELETE FROM openrouter_models WHERE llm_provider_config_id = $1",
            provider_uuid
        )

        # Insert models from pricing database
        for model_id, pricing in OPENROUTER_PRICING_DB.items():
            model_uuid = uuid.uuid4()

            await conn.execute(
                """
                INSERT INTO openrouter_models (
                    id, llm_provider_config_id, model_id, model_name, provider_name,
                    context_length, input_cost_per_million, output_cost_per_million,
                    supports_streaming, supports_function_calling, supports_vision,
                    created_at, updated_at, discovered_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    NOW(), NOW(), NOW()
                )
                """,
                model_uuid, provider_uuid, model_id, model_id, pricing.model_id.split('/')[0],
                pricing.context_window, float(pricing.input_cost_per_million),
                float(pricing.output_cost_per_million),
                True, True, False  # Assuming streaming and function calling support
            )

            models_synced += 1

    return models_synced


async def get_provider_models(provider_id: str) -> List[Dict[str, Any]]:
    """Get all models for a provider."""
    config = await get_provider_config(provider_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider configuration not found"
        )

    # Return mock models from pricing database
    models = []
    for model_id, pricing in OPENROUTER_PRICING_DB.items():
        models.append({
            "id": str(uuid.uuid4()),
            "llm_provider_config_id": provider_id,
            "model_id": model_id,
            "model_name": model_id,
            "provider_name": model_id.split('/')[0],
            "context_length": pricing.context_window,
            "input_cost_per_million": float(pricing.input_cost_per_million),
            "output_cost_per_million": float(pricing.output_cost_per_million),
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": False,
            "is_available": True,
            "total_requests": 0,
            "total_cost_usd": 0.0
        })

    return models


async def perform_health_check(provider_id: str) -> HealthCheckResponse:
    """Perform a health check on the OpenRouter provider."""
    import time
    import httpx

    config = await get_provider_config(provider_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider configuration not found"
        )

    start_time = time.time()
    is_healthy = False
    error_message = None
    response_time_ms = None

    try:
        # Make a simple request to OpenRouter API
        headers = {"Authorization": f"Bearer {config.api_key_encrypted}"}
        if config.custom_headers:
            headers.update(config.custom_headers)

        with httpx.Client(timeout=config.connection_timeout_seconds) as client:
            response = client.get(
                f"{config.api_base_url}/models",
                headers=headers
            )

            response_time_ms = (time.time() - start_time) * 1000
            is_healthy = response.status_code == 200

            if not is_healthy:
                error_message = f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        error_message = str(e)
        logger.error(f"Health check failed for provider {provider_id}: {e}")

    # Update provider health status
    async with database.get_connection() as conn:
        await conn.execute(
            """
            UPDATE llm_provider_configs
            SET health_status = $1, last_health_check_at = NOW(),
                last_error_at = CASE WHEN $2 THEN NULL ELSE NOW() END,
                last_error_message = CASE WHEN $2 THEN NULL ELSE $3 END,
                consecutive_errors = CASE WHEN $2 THEN 0 ELSE consecutive_errors + 1 END
            WHERE id = $4
            """,
            "healthy" if is_healthy else "unhealthy",
            is_healthy, error_message, uuid.UUID(provider_id)
        )

    return HealthCheckResponse(
        provider_id=provider_id,
        provider_name=config.provider_name,
        status="healthy" if is_healthy else "unhealthy",
        is_healthy=is_healthy,
        response_time_ms=response_time_ms,
        error_message=error_message,
        checked_at=datetime.now(timezone.utc),
        uptime_percentage=config.uptime_percentage,
        consecutive_errors=config.consecutive_errors,
        last_error_at=config.last_error_at,
        last_request_at=config.last_request_at
    )


async def get_provider_statistics(provider_id: str) -> ProviderStatsResponse:
    """Get comprehensive statistics for a provider."""
    config = await get_provider_config(provider_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider configuration not found"
        )

    # Get model usage statistics
    async with database.get_connection() as conn:
        # Most used models
        most_used_models = await conn.fetch(
            """
            SELECT model_id, total_requests, total_cost_usd
            FROM openrouter_models
            WHERE llm_provider_config_id = $1 AND total_requests > 0
            ORDER BY total_requests DESC
            LIMIT 5
            """,
            uuid.UUID(provider_id)
        )

        # Calculate error rate
        error_rate = 0.0
        if config.total_requests > 0:
            error_rate = (config.consecutive_errors / config.total_requests) * 100

    return ProviderStatsResponse(
        provider_id=provider_id,
        provider_name=config.provider_name,
        total_requests=config.total_requests,
        total_tokens=config.total_tokens,
        total_cost_usd=config.total_cost_usd,
        average_cost_per_request=config.total_cost_usd / max(config.total_requests, 1),
        average_tokens_per_request=config.total_tokens / max(config.total_requests, 1),
        uptime_percentage=config.uptime_percentage,
        error_rate=error_rate,
        last_request_at=config.last_request_at,
        most_used_models=[dict(row) for row in most_used_models],
        cost_breakdown={}  # Could be enhanced with detailed cost breakdown
    )


# ═══════════════════════════════════════════════════════════
# API Endpoint Functions
# ═══════════════════════════════════════════════════════════


async def create_openrouter_provider(request: OpenRouterProviderCreate) -> OpenRouterProviderResponse:
    """Create a new OpenRouter provider configuration."""
    try:
        logger.http_request("POST", "/api/openrouter/providers")

        # Validate display name
        if not request.display_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Display name is required"
            )

        config = await create_provider_config(request)

        # Sync models from pricing database
        await sync_openrouter_models(config["id"])

        logger.http_request("POST", "/api/openrouter/providers", 201)
        return OpenRouterProviderResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create OpenRouter provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def get_openrouter_providers() -> List[OpenRouterProviderResponse]:
    """List all OpenRouter provider configurations."""
    try:
        logger.http_request("GET", "/api/openrouter/providers")

        configs = await list_provider_configs()

        # Filter for OpenRouter providers only
        openrouter_configs = [
            config for config in configs
            if config.get("provider_type") == "openrouter"
        ]

        logger.http_request("GET", "/api/openrouter/providers", 200)
        return [OpenRouterProviderResponse(**config) for config in openrouter_configs]

    except Exception as e:
        logger.error(f"Failed to list OpenRouter providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def get_openrouter_provider(provider_id: str) -> OpenRouterProviderResponse:
    """Get a specific OpenRouter provider configuration."""
    try:
        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}")

        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.get("provider_type") != "openrouter":
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}", 200)
        return OpenRouterProviderResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OpenRouter provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def update_openrouter_provider(
    provider_id: str,
    request: OpenRouterProviderUpdate
) -> OpenRouterProviderResponse:
    """Update an OpenRouter provider configuration."""
    try:
        logger.http_request("PUT", f"/api/openrouter/providers/{provider_id}")

        config = await update_provider_config(provider_id, request)
        if not config:
            logger.http_request("PUT", f"/api/openrouter/providers/{provider_id}", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("PUT", f"/api/openrouter/providers/{provider_id}", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        logger.http_request("PUT", f"/api/openrouter/providers/{provider_id}", 200)
        return OpenRouterProviderResponse(**config.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update OpenRouter provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def delete_openrouter_provider(provider_id: str) -> Dict[str, str]:
    """Delete an OpenRouter provider configuration."""
    try:
        logger.http_request("DELETE", f"/api/openrouter/providers/{provider_id}")

        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("DELETE", f"/api/openrouter/providers/{provider_id}", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("DELETE", f"/api/openrouter/providers/{provider_id}", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        success = await delete_provider_config(provider_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete provider configuration"
            )

        logger.http_request("DELETE", f"/api/openrouter/providers/{provider_id}", 200)
        return {"message": "Provider configuration deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete OpenRouter provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def list_openrouter_models(provider_id: str) -> ModelListResponse:
    """List all available models for an OpenRouter provider."""
    try:
        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/models")

        # Verify provider exists and is OpenRouter
        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/models", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/models", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        models = await get_provider_models(provider_id)

        # Also include models from pricing database
        pricing_models = []
        for model_id, pricing in OPENROUTER_PRICING_DB.items():
            pricing_models.append({
                "model_id": model_id,
                "model_name": model_id,
                "provider_name": pricing.model_id.split('/')[0],
                "context_length": pricing.context_window,
                "input_cost_per_million": float(pricing.input_cost_per_million),
                "output_cost_per_million": float(pricing.output_cost_per_million),
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "pricing_available": True
            })

        # Combine database models and pricing models
        all_models = []

        # Add models from database
        for model in models:
            all_models.append({
                "id": str(model.id),
                "model_id": model.model_id,
                "model_name": model.model_name,
                "provider_name": model.provider_name,
                "context_length": model.context_length,
                "input_cost_per_million": model.input_cost_per_million,
                "output_cost_per_million": model.output_cost_per_million,
                "supports_streaming": model.supports_streaming,
                "supports_function_calling": model.supports_function_calling,
                "supports_vision": model.supports_vision,
                "total_requests": model.total_requests,
                "total_cost_usd": model.total_cost_usd,
                "is_available": model.is_available,
                "pricing_available": True,
                "source": "database"
            })

        # Add pricing models that aren't in database
        existing_model_ids = {model["model_id"] for model in all_models}
        for pricing_model in pricing_models:
            if pricing_model["model_id"] not in existing_model_ids:
                pricing_model["source"] = "pricing_db"
                all_models.append(pricing_model)

        # Sort by model name
        all_models.sort(key=lambda x: x["model_name"])

        # Count unique providers
        providers = set(model["provider_name"] for model in all_models)

        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/models", 200)
        return ModelListResponse(
            models=all_models,
            total_count=len(all_models),
            provider_count=len(providers),
            last_updated=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list OpenRouter models for provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def estimate_request_cost(request: CostEstimationRequest) -> CostEstimationResponse:
    """Estimate the cost of a request using OpenRouter pricing."""
    try:
        logger.http_request("POST", "/api/openrouter/cost-estimate")

        # Check if model exists in pricing database
        pricing = get_model_pricing(request.model_id)
        if not pricing:
            logger.http_request("POST", "/api/openrouter/cost-estimate", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.model_id}' not found in pricing database"
            )

        # Calculate estimated cost
        estimated_cost = estimate_cost(
            model_id=request.model_id,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cache_read_tokens=request.cache_read_tokens,
            cache_write_tokens=request.cache_write_tokens
        )

        # Calculate context usage percentage
        context_window = get_model_context_window(request.model_id)
        context_usage = None
        if context_window:
            context_usage = calculate_context_usage_percentage(
                request.model_id,
                request.input_tokens
            )

        # Prepare pricing info
        pricing_info = {
            "input_cost_per_million": float(pricing.input_cost_per_million),
            "output_cost_per_million": float(pricing.output_cost_per_million),
            "context_window": pricing.context_window,
            "currency": "USD"
        }

        if pricing.cache_read_cost_per_million:
            pricing_info["cache_read_cost_per_million"] = float(pricing.cache_read_cost_per_million)
        if pricing.cache_write_cost_per_million:
            pricing_info["cache_write_cost_per_million"] = float(pricing.cache_write_cost_per_million)

        logger.http_request("POST", "/api/openrouter/cost-estimate", 200)
        return CostEstimationResponse(
            model_id=request.model_id,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cache_read_tokens=request.cache_read_tokens,
            cache_write_tokens=request.cache_write_tokens,
            estimated_cost_usd=float(estimated_cost) if estimated_cost else None,
            context_window=context_window,
            context_usage_percentage=context_usage,
            pricing_info=pricing_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def check_provider_health(provider_id: str) -> HealthCheckResponse:
    """Perform a health check on an OpenRouter provider."""
    try:
        logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/health")

        # Verify provider exists and is OpenRouter
        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/health", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/health", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        health_result = await perform_health_check(provider_id)

        logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/health", 200)
        return health_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check provider health {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def get_provider_stats(provider_id: str) -> ProviderStatsResponse:
    """Get comprehensive statistics for an OpenRouter provider."""
    try:
        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/stats")

        # Verify provider exists and is OpenRouter
        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/stats", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/stats", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        stats = await get_provider_statistics(provider_id)

        logger.http_request("GET", f"/api/openrouter/providers/{provider_id}/stats", 200)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider statistics {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def sync_provider_models(provider_id: str) -> Dict[str, Any]:
    """Sync models for an OpenRouter provider from the pricing database."""
    try:
        logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/sync-models")

        # Verify provider exists and is OpenRouter
        config = await get_provider_config(provider_id)
        if not config:
            logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/sync-models", 404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )

        if config.provider_type != "openrouter":
            logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/sync-models", 400)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not an OpenRouter provider"
            )

        models_synced = await sync_openrouter_models(provider_id)

        logger.http_request("POST", f"/api/openrouter/providers/{provider_id}/sync-models", 200)
        return {
            "message": f"Successfully synced {models_synced} models",
            "models_synced": models_synced,
            "provider_id": provider_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync provider models {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ═══════════════════════════════════════════════════════════
# Export All Functions
# ═══════════════════════════════════════════════════════════

__all__ = [
    # Pydantic Models
    "OpenRouterProviderCreate",
    "OpenRouterProviderUpdate",
    "OpenRouterProviderResponse",
    "OpenRouterModelResponse",
    "CostEstimationRequest",
    "CostEstimationResponse",
    "HealthCheckResponse",
    "ModelListResponse",
    "ProviderStatsResponse",

    # API Endpoint Functions
    "create_openrouter_provider",
    "get_openrouter_providers",
    "get_openrouter_provider",
    "update_openrouter_provider",
    "delete_openrouter_provider",
    "list_openrouter_models",
    "estimate_request_cost",
    "check_provider_health",
    "get_provider_stats",
    "sync_provider_models",

    # Helper Functions
    "get_provider_config",
    "list_provider_configs",
    "perform_health_check",
    "sync_openrouter_models",
]