"""
Test script for OpenRouter Provider Configuration API Endpoints

This script tests the basic functionality of the OpenRouter endpoints
without requiring a full database setup. It can be used for validation
during development.
"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_imports():
    """Test that all imports work correctly."""
    try:
        print("Testing imports...")

        # Test openrouter_endpoints imports
        from modules.openrouter_endpoints import (
            OpenRouterProviderCreate,
            OpenRouterProviderUpdate,
            OpenRouterProviderResponse,
            CostEstimationRequest,
            CostEstimationResponse,
            HealthCheckResponse,
            ModelListResponse,
            ProviderStatsResponse,
        )
        print("✅ OpenRouter endpoint models imported successfully")

        # Test openrouter_routes imports
        from openrouter_routes import router
        print("✅ OpenRouter routes imported successfully")

        # Test openrouter_client imports
        from modules.openrouter_client import (
            OPENROUTER_PRICING_DB,
            ModelPricing,
            estimate_cost,
            get_model_context_window,
            list_available_models,
            get_model_pricing,
        )
        print("✅ OpenRouter client imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False


async def test_pydantic_models():
    """Test Pydantic model validation."""
    try:
        print("\nTesting Pydantic models...")

        from modules.openrouter_endpoints import (
            OpenRouterProviderCreate,
            CostEstimationRequest,
        )

        # Test OpenRouterProviderCreate
        provider_data = {
            "display_name": "Test OpenRouter Provider",
            "provider_description": "A test provider configuration",
            "api_key_encrypted": "encrypted_api_key_here",
            "rate_limit_rpm": 100,
            "rate_limit_tpm": 50000,
            "tags": ["test", "openrouter"],
            "metadata": {"test": True}
        }

        provider = OpenRouterProviderCreate(**provider_data)
        print(f"✅ OpenRouterProviderCreate validation passed: {provider.display_name}")

        # Test CostEstimationRequest
        cost_data = {
            "model_id": "anthropic/claude-3.5-sonnet",
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_tokens": 100,
            "cache_write_tokens": 50
        }

        cost_request = CostEstimationRequest(**cost_data)
        print(f"✅ CostEstimationRequest validation passed: {cost_request.model_id}")

        return True

    except Exception as e:
        print(f"❌ Pydantic model validation error: {e}")
        return False


async def test_openrouter_client():
    """Test OpenRouter client functionality."""
    try:
        print("\nTesting OpenRouter client...")

        from modules.openrouter_client import (
            OPENROUTER_PRICING_DB,
            estimate_cost,
            get_model_context_window,
            list_available_models,
            get_model_pricing,
        )

        # Test model listing
        models = list_available_models()
        print(f"✅ Found {len(models)} models in pricing database")

        # Test pricing lookup
        test_model = "anthropic/claude-3.5-sonnet"
        pricing = get_model_pricing(test_model)
        if pricing:
            print(f"✅ Found pricing for {test_model}: ${float(pricing.input_cost_per_million)}/M input tokens")
        else:
            print(f"⚠️  No pricing found for {test_model}")

        # Test cost estimation
        estimated_cost = estimate_cost(
            model_id=test_model,
            input_tokens=1000,
            output_tokens=500
        )
        if estimated_cost:
            print(f"✅ Cost estimation for {test_model}: ${float(estimated_cost):.6f}")

        # Test context window
        context_window = get_model_context_window(test_model)
        if context_window:
            print(f"✅ Context window for {test_model}: {context_window:,} tokens")

        return True

    except Exception as e:
        print(f"❌ OpenRouter client error: {e}")
        return False


async def test_route_definitions():
    """Test route definitions and structure."""
    try:
        print("\nTesting route definitions...")

        from openrouter_routes import router

        # Check that router has routes
        routes = router.routes
        print(f"✅ OpenRouter router has {len(routes)} routes defined")

        # Print route information
        for route in routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else []
                print(f"  📋 {methods} {route.path}")

        return True

    except Exception as e:
        print(f"❌ Route definition error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing OpenRouter Provider Configuration API")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Pydantic Model Tests", test_pydantic_models),
        ("OpenRouter Client Tests", test_openrouter_client),
        ("Route Definition Tests", test_route_definitions),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)

        try:
            if await test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! OpenRouter endpoints are ready for integration.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)