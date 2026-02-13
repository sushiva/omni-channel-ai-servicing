"""
Quick test script to verify guardrails validation
"""
from omni_channel_ai_servicing.services.guardrails import GuardrailService

# Initialize guardrails
guardrails = GuardrailService()

print("=" * 60)
print("GUARDRAILS VALIDATION TESTS")
print("=" * 60)

# Test 1: Clean request (should pass)
print("\n1. Testing clean banking request:")
text = "I need to update my mailing address"
is_safe, violations = guardrails.validate_input(text, "CUST123")
print(f"   Input: {text}")
print(f"   Safe: {is_safe}")
print(f"   Violations: {len(violations)}")

# Test 2: PII in request (should fail)
print("\n2. Testing request with SSN (should block):")
text = "My SSN is 123-45-6789, can you help?"
is_safe, violations = guardrails.validate_input(text, "CUST123")
print(f"   Input: {text}")
print(f"   Safe: {is_safe}")
print(f"   Violations: {[v.message for v in violations]}")

# Test 3: SQL injection attempt (should block)
print("\n3. Testing SQL injection (should block):")
text = "SELECT * FROM users; DROP TABLE customers;"
is_safe, violations = guardrails.validate_input(text, "CUST123")
print(f"   Input: {text}")
print(f"   Safe: {is_safe}")
print(f"   Violations: {[v.message for v in violations]}")

# Test 4: Off-topic request (should warn)
print("\n4. Testing off-topic request (should warn):")
text = "What's the weather like today?"
is_safe, violations = guardrails.validate_input(text, "CUST123")
print(f"   Input: {text}")
print(f"   Safe: {is_safe}")
print(f"   Violations: {[v.message for v in violations]}")

# Test 5: Output with hallucinated policy number (should block)
print("\n5. Testing output with fake policy number (should block):")
response = "Your policy #1234567890123 has been updated"
is_safe, violations = guardrails.validate_output(response, {}, "update policy")
print(f"   Output: {response}")
print(f"   Safe: {is_safe}")
print(f"   Violations: {[v.message for v in violations]}")

# Test 6: Confidence threshold
print("\n6. Testing low confidence routing:")
should_proceed, reason = guardrails.check_confidence_threshold(0.5, "address_update")
print(f"   Confidence: 0.5")
print(f"   Should proceed: {should_proceed}")
print(f"   Reason: {reason}")

print("\n" + "=" * 60)
print("GUARDRAILS TEST COMPLETE")
print("=" * 60)
