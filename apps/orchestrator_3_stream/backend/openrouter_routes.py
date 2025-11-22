"""
OpenRouter Provider Configuration API Routes

FastAPI route definitions for OpenRouter provider management endpoints.
These routes provide comprehensive CRUD operations, model listing, cost estimation,
and health checks for OpenRouter provider configurations.

Usage:
    from fastapi import FastAPI
    from openrouter_routes import router as openrouter_router

    app = FastAPI()
    app.include_router(openrouter_router, prefix="/api/openrouter", tags=["OpenRouter"])
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional

from modules.openrouter_endpoints import (
    # Request/Response Models
    OpenRouterProviderCreate,
    OpenRouterProviderUpdate,
    OpenRouterProviderResponse,
    OpenRouterModelResponse,
    CostEstimationRequest,
    CostEstimationResponse,
    HealthCheckResponse,
    ModelListResponse,
    ProviderStatsResponse,

    # API Endpoint Functions
    create_openrouter_provider,
    get_openrouter_providers,
    get_openrouter_provider,
    update_openrouter_provider,
    delete_openrouter_provider,
    list_openrouter_models,
    estimate_request_cost,
    check_provider_health,
    get_provider_stats,
    sync_provider_models,
)

# Create router
router = APIRouter()


# ═══════════════════════════════════════════════════════════
# Provider Configuration CRUD Routes
# ═══════════════════════════════════════════════════════════


@router.post(
    "/providers",
    response_model=OpenRouterProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create OpenRouter Provider",
    description="Create a new OpenRouter provider configuration with specified settings."
)
async def create_provider(request: OpenRouterProviderCreate):
    """Create a new OpenRouter provider configuration."""
    return await create_openrouter_provider(request)


@router.get(
    "/providers",
    response_model=List[OpenRouterProviderResponse],
    summary="List OpenRouter Providers",
    description="List all OpenRouter provider configurations for the current orchestrator."
)
async def list_providers():
    """List all OpenRouter provider configurations."""
    return await get_openrouter_providers()


@router.get(
    "/providers/{provider_id}",
    response_model=OpenRouterProviderResponse,
    summary="Get OpenRouter Provider",
    description="Get a specific OpenRouter provider configuration by ID."
)
async def get_provider(provider_id: str):
    """Get a specific OpenRouter provider configuration."""
    return await get_openrouter_provider(provider_id)


@router.put(
    "/providers/{provider_id}",
    response_model=OpenRouterProviderResponse,
    summary="Update OpenRouter Provider",
    description="Update an existing OpenRouter provider configuration."
)
async def update_provider(provider_id: str, request: OpenRouterProviderUpdate):
    """Update an existing OpenRouter provider configuration."""
    return await update_openrouter_provider(provider_id, request)


@router.delete(
    "/providers/{provider_id}",
    summary="Delete OpenRouter Provider",
    description="Soft delete an OpenRouter provider configuration."
)
async def delete_provider(provider_id: str):
    """Soft delete an OpenRouter provider configuration."""
    return await delete_openrouter_provider(provider_id)


# ═══════════════════════════════════════════════════════════
# Model Management Routes
# ═══════════════════════════════════════════════════════════


@router.get(
    "/providers/{provider_id}/models",
    response_model=ModelListResponse,
    summary="List OpenRouter Models",
    description="List all available models for an OpenRouter provider, including pricing information."
)
async def get_provider_models(
    provider_id: str,
    include_pricing: bool = Query(True, description="Include pricing information"),
    filter_available: bool = Query(False, description="Filter to only available models"),
    provider_filter: Optional[str] = Query(None, description="Filter by provider name")
):
    """List all available models for an OpenRouter provider."""
    model_list = await list_openrouter_models(provider_id)

    # Apply filters
    if filter_available:
        model_list.models = [m for m in model_list.models if m.get("is_available", True)]

    if provider_filter:
        model_list.models = [m for m in model_list.models
                           if m.get("provider_name", "").lower() == provider_filter.lower()]

    if not include_pricing:
        for model in model_list.models:
            model.pop("input_cost_per_million", None)
            model.pop("output_cost_per_million", None)
            model.pop("pricing_info", None)

    return model_list


@router.post(
    "/providers/{provider_id}/sync-models",
    summary="Sync Provider Models",
    description="Sync models from the OpenRouter pricing database to the local database."
)
async def sync_models(provider_id: str):
    """Sync models from the OpenRouter pricing database."""
    return await sync_provider_models(provider_id)


# ═══════════════════════════════════════════════════════════
# Cost Estimation Routes
# ═══════════════════════════════════════════════════════════


@router.post(
    "/cost-estimate",
    response_model=CostEstimationResponse,
    summary="Estimate Request Cost",
    description="Estimate the cost of a request using OpenRouter pricing information."
)
async def estimate_cost(request: CostEstimationRequest):
    """Estimate the cost of a request using OpenRouter pricing."""
    return await estimate_request_cost(request)


@router.get(
    "/models/{model_id}/pricing",
    summary="Get Model Pricing",
    description="Get detailed pricing information for a specific OpenRouter model."
)
async def get_model_pricing(model_id: str):
    """Get detailed pricing information for a specific model."""
    from modules.openrouter_client import get_model_pricing

    pricing = get_model_pricing(model_id)
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found in pricing database"
        )

    return {
        "model_id": model_id,
        "input_cost_per_million": float(pricing.input_cost_per_million),
        "output_cost_per_million": float(pricing.output_cost_per_million),
        "cache_read_cost_per_million": float(pricing.cache_read_cost_per_million) if pricing.cache_read_cost_per_million else None,
        "cache_write_cost_per_million": float(pricing.cache_write_cost_per_million) if pricing.cache_write_cost_per_million else None,
        "context_window": pricing.context_window,
        "currency": "USD"
    }


# ═══════════════════════════════════════════════════════════
# Health Check Routes
# ═══════════════════════════════════════════════════════════


@router.post(
    "/providers/{provider_id}/health",
    response_model=HealthCheckResponse,
    summary="Check Provider Health",
    description="Perform a health check on an OpenRouter provider configuration."
)
async def check_health(provider_id: str):
    """Perform a health check on an OpenRouter provider."""
    return await check_provider_health(provider_id)


@router.get(
    "/providers/{provider_id}/stats",
    response_model=ProviderStatsResponse,
    summary="Get Provider Statistics",
    description="Get comprehensive statistics and usage metrics for an OpenRouter provider."
)
async def get_stats(provider_id: str):
    """Get comprehensive statistics for an OpenRouter provider."""
    return await get_provider_stats(provider_id)


# ═══════════════════════════════════════════════════════════
# Utility Routes
# ═══════════════════════════════════════════════════════════


@router.get(
    "/models/available",
    summary="List Available Models",
    description="Get a list of all available models from the OpenRouter pricing database."
)
async def get_available_models():
    """Get a list of all available models from the pricing database."""
    from modules.openrouter_client import list_available_models, get_model_pricing

    model_ids = list_available_models()
    models = []

    for model_id in model_ids:
        pricing = get_model_pricing(model_id)
        if pricing:
            models.append({
                "model_id": model_id,
                "model_name": model_id,
                "provider_name": model_id.split('/')[0],
                "context_window": pricing.context_window,
                "input_cost_per_million": float(pricing.input_cost_per_million),
                "output_cost_per_million": float(pricing.output_cost_per_million),
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": False,
            })

    return {
        "models": models,
        "total_count": len(models),
        "last_updated": "2024-01-01T00:00:00Z"  # This could be dynamic
    }


@router.get(
    "/providers/{provider_id}/test-connection",
    summary="Test Provider Connection",
    description="Test the connection to an OpenRouter provider without performing a full health check."
)
async def test_connection(provider_id: str):
    """Test the connection to an OpenRouter provider."""
    import httpx

    from modules.openrouter_endpoints import get_provider_config

    config = await get_provider_config(provider_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider configuration not found"
        )

    if config.provider_type != "openrouter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not an OpenRouter provider"
        )

    try:
        headers = {"Authorization": f"Bearer {config.api_key_encrypted}"}
        if config.custom_headers:
            headers.update(config.custom_headers)

        with httpx.Client(timeout=config.connection_timeout_seconds) as client:
            response = client.get(
                f"{config.api_base_url}/models",
                headers=headers
            )

        return {
            "status": "success" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "message": "Connection successful" if response.status_code == 200 else f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            "status": "error",
            "status_code": None,
            "response_time_ms": None,
            "message": str(e)
        }


@router.get(
    "/models/{model_id}/context-usage",
    summary="Calculate Context Usage",
    description="Calculate context usage percentage for a given model and token count."
)
async def calculate_context_usage(
    model_id: str,
    input_tokens: int = Query(..., ge=0, description="Number of input tokens")
):
    """Calculate context usage percentage for a model."""
    from modules.openrouter_client import (
        get_model_context_window,
        calculate_context_usage_percentage
    )

    context_window = get_model_context_window(model_id)
    if not context_window:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context window not available for model '{model_id}'"
        )

    usage_percentage = calculate_context_usage_percentage(model_id, input_tokens)

    return {
        "model_id": model_id,
        "input_tokens": input_tokens,
        "context_window": context_window,
        "context_usage_percentage": usage_percentage,
        "remaining_tokens": max(0, context_window - input_tokens),
        "usage_category": (
            "low" if usage_percentage < 50 else
            "medium" if usage_percentage < 80 else
            "high" if usage_percentage < 95 else
            "critical"
        )
    }