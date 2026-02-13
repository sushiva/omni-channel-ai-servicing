"""
Test guardrails through API requests
Start the API server first: make run-api
Then run this script in another terminal
"""
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 60)
print("API GUARDRAILS TEST")
print("=" * 60)

# Test requests
test_cases = [
    {
        "name": "Clean request",
        "email_body": "I need to update my address to 123 Main St",
        "expected": "Should process normally"
    },
    {
        "name": "Request with SSN",
        "email_body": "My SSN is 123-45-6789, please help",
        "expected": "Should be blocked by guardrails"
    },
    {
        "name": "SQL injection attempt",
        "email_body": "email'; DROP TABLE users; --",
        "expected": "Should be blocked"
    },
    {
        "name": "Credit card number",
        "email_body": "My card 4532-1234-5678-9010 was charged",
        "expected": "Should detect PII"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Input: {test['email_body']}")
    print(f"   Expected: {test['expected']}")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/service-request",
            json={
                "message": test['email_body'],
                "customer_id": "TEST_CUST_001",
                "channel": "email"
            },
            timeout=5
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', 'N/A')[:100]}")
        else:
            print(f"   Error: {response.text[:100]}")
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  API not running. Start it with: make run-api")
        break
    except Exception as e:
        print(f"   Error: {str(e)}")

print("\n" + "=" * 60)
