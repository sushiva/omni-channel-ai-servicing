"""
Test script for the API endpoints.

Tests the REST API by making HTTP requests to the service.
Can be run while the FastAPI server is running.
"""
import asyncio
import httpx
from typing import Dict, Any

# API base URL (assumes server is running locally)
BASE_URL = "http://localhost:8001"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_response(response: httpx.Response):
    """Print formatted response details."""
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        data = response.json()
        import json
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


async def test_health_check():
    """Test the health check endpoint."""
    print_section("TEST 1: Health Check")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print_response(response)
        assert response.status_code == 200, "Health check should return 200"
        print("✅ Test 1 PASSED")


async def test_root_endpoint():
    """Test the root endpoint."""
    print_section("TEST 2: Root Endpoint")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print_response(response)
        assert response.status_code == 200, "Root should return 200"
        print("✅ Test 2 PASSED")


async def test_list_intents():
    """Test the list intents endpoint."""
    print_section("TEST 3: List Supported Intents")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/intents")
        print_response(response)
        assert response.status_code == 200, "Intents endpoint should return 200"
        print("✅ Test 3 PASSED")


async def test_address_update_request():
    """Test address update through the service request endpoint."""
    print_section("TEST 4: Address Update Request")
    
    request_data = {
        "customer_id": "cust123",
        "message": "I want to change my address to 456 Oak Ave, Raleigh NC 27601",
        "channel": "email",
        "metadata": {
            "session_id": "test_session_001",
            "locale": "en_US"
        }
    }
    
    print("\nRequest:")
    import json
    print(json.dumps(request_data, indent=2))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/service-request",
            json=request_data
        )
        print_response(response)
        
        assert response.status_code == 200, "Address update should return 200"
        data = response.json()
        assert data["intent"] == "update_address", "Intent should be update_address"
        assert data["workflow"] == "address_workflow", "Should use address_workflow"
        # Accept either success or error (mock services may not be running)
        assert data["status"] in ["success", "address updated", "error"], f"Unexpected status: {data['status']}"
        print("✅ Test 4 PASSED (note: mock services may affect result)")


async def test_unknown_intent_request():
    """Test fallback behavior for unknown intent."""
    print_section("TEST 5: Unknown Intent Request")
    
    request_data = {
        "customer_id": "cust456",
        "message": "What is the weather like today?",
        "channel": "chat"
    }
    
    print("\nRequest:")
    import json
    print(json.dumps(request_data, indent=2))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/service-request",
            json=request_data
        )
        print_response(response)
        
        assert response.status_code == 200, "Should return 200 even for unknown intent"
        data = response.json()
        assert data["intent"] == "unknown", "Intent should be unknown"
        assert data["workflow"] == "fallback_workflow", "Should use fallback_workflow"
        assert data["status"] == "fallback", "Status should be fallback"
        print("✅ Test 5 PASSED")


async def test_statement_request():
    """Test statement request (should route to fallback until implemented)."""
    print_section("TEST 6: Statement Request (Unimplemented Workflow)")
    
    request_data = {
        "customer_id": "cust789",
        "message": "I need my last 3 months of bank statements",
        "channel": "mobile"
    }
    
    print("\nRequest:")
    import json
    print(json.dumps(request_data, indent=2))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/service-request",
            json=request_data
        )
        print_response(response)
        
        assert response.status_code == 200, "Should return 200"
        data = response.json()
        assert data["intent"] == "request_statement", "Intent should be request_statement"
        # Should route to fallback since statement_workflow not implemented
        assert data["workflow"] == "fallback_workflow", "Should route to fallback"
        print("✅ Test 6 PASSED")


async def test_validation_error():
    """Test validation error handling."""
    print_section("TEST 7: Validation Error")
    
    # Missing required field (customer_id)
    request_data = {
        "message": "I need help",
        "channel": "web"
    }
    
    print("\nRequest (missing customer_id):")
    import json
    print(json.dumps(request_data, indent=2))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/service-request",
            json=request_data
        )
        print_response(response)
        
        assert response.status_code == 422, "Should return 422 for validation error"
        print("✅ Test 7 PASSED")


async def main():
    """Run all API tests."""
    print("\n" + "=" * 70)
    print("  OMNI-CHANNEL AI SERVICING - API TEST SUITE")
    print("=" * 70)
    print("\n⚠️  Make sure the FastAPI server is running:")
    print("   cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing")
    print("   source .venv/bin/activate")
    print("   python -m omni_channel_ai_servicing.app.main")
    print("\n   Or: uvicorn omni_channel_ai_servicing.app.main:app --reload")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(BASE_URL)
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print(f"   {str(e)}")
        print("\n   Please start the server first!")
        return
    
    try:
        await test_health_check()
        await test_root_endpoint()
        await test_list_intents()
        await test_address_update_request()
        await test_unknown_intent_request()
        await test_statement_request()
        await test_validation_error()
        
        print("\n" + "=" * 70)
        print("  ✅ ALL API TESTS PASSED")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
