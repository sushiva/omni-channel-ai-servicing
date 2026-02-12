"""
Unit tests for guardrails service.
"""
import pytest
from omni_channel_ai_servicing.services.guardrails import GuardrailService, SYSTEM_PROMPT_GUARDRAILS, get_guardrail_prompt


class TestGuardrailService:
    """Test the GuardrailService class"""
    
    def setup_method(self):
        """Create a fresh guardrail service for each test"""
        self.guardrails = GuardrailService()
    
    # ============= Input Validation Tests =============
    
    def test_clean_banking_request(self):
        """Test that clean banking requests pass validation"""
        text = "I need to update my mailing address to 123 Main St, New York, NY 10001"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        assert is_safe is True
        assert len(violations) == 0
    
    def test_detect_ssn_in_input(self):
        """Test detection of SSN in user input"""
        text = "My SSN is 123-45-6789 and I need help"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        assert is_safe is False
        assert any(v.rule == "pii_ssn" for v in violations)
        assert any(v.severity == "error" for v in violations)
    
    def test_detect_credit_card_in_input(self):
        """Test detection of credit card number"""
        text = "My card number is 4532-1234-5678-9010"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        assert is_safe is False
        assert any(v.rule == "pii_credit_card" for v in violations)
    
    def test_detect_phone_in_input(self):
        """Test detection of phone numbers"""
        text = "Call me at 555-123-4567"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        assert is_safe is False
        assert any(v.rule == "pii_phone" for v in violations)
    
    def test_detect_profanity_warning(self):
        """Test profanity detection (warning level)"""
        text = "This damn system never works!"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        # Profanity is warning, not error - still safe to process
        assert is_safe is True
        assert any(v.rule == "profanity" for v in violations)
        assert all(v.severity == "warning" for v in violations if v.rule == "profanity")
    
    def test_detect_sql_injection(self):
        """Test SQL injection attempt detection"""
        text = "'; DROP TABLE users; --"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        assert is_safe is False
        assert any(v.rule == "injection_attempt" for v in violations)
    
    def test_detect_off_topic_request(self):
        """Test off-topic request detection"""
        text = "What's the weather like today?"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        # Off-topic is warning, not error
        assert is_safe is True
        assert any(v.rule == "off_topic" for v in violations)
    
    # ============= Output Validation Tests =============
    
    def test_clean_banking_response(self):
        """Test that clean responses pass validation"""
        response = "I've updated your mailing address as requested. You should receive confirmation shortly."
        user_input = "Update my address"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123", "intent": "update_address"}, user_input
        )
        
        assert is_safe is True
        assert len([v for v in violations if v.severity == "error"]) == 0
    
    def test_detect_hallucinated_policy_number(self):
        """Test detection of fake policy numbers"""
        response = "Your request is under policy #12345678901234567890"
        user_input = "I need help"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        assert is_safe is False
        assert any("hallucination" in v.rule for v in violations)
    
    def test_detect_hallucinated_account_number(self):
        """Test detection of fake account numbers"""
        response = "Your account #123456789012345678 has been updated"
        user_input = "Update my account"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        assert is_safe is False
        assert any("hallucination" in v.rule for v in violations)
    
    def test_detect_pii_in_response(self):
        """Test PII detection in LLM response"""
        response = "Your SSN 123-45-6789 has been verified"
        user_input = "Verify my identity"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        assert is_safe is False
        assert any(v.rule == "pii_ssn" for v in violations)
    
    def test_detect_too_short_response(self):
        """Test detection of unhelpful short responses"""
        response = "OK"
        user_input = "I need help with my account"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        # Short response is warning, not error
        assert is_safe is True
        assert any(v.rule == "response_too_short" for v in violations)
    
    def test_detect_generic_fallback_response(self):
        """Test detection of generic 'I don't know' responses"""
        response = "I don't know how to help with that"
        user_input = "Update my address"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        # Generic response is warning
        assert is_safe is True
        assert any(v.rule == "generic_response" for v in violations)
    
    # ============= Confidence Threshold Tests =============
    
    def test_high_confidence_passes(self):
        """Test high confidence allows processing"""
        should_proceed, reason = self.guardrails.check_confidence_threshold(
            confidence=0.95,
            intent="update_address"
        )
        
        assert should_proceed is True
        assert reason is None
    
    def test_low_confidence_blocks(self):
        """Test low confidence routes to human"""
        should_proceed, reason = self.guardrails.check_confidence_threshold(
            confidence=0.45,
            intent="update_address"
        )
        
        assert should_proceed is False
        assert "Low confidence" in reason
        assert "routing to human agent" in reason
    
    def test_borderline_confidence(self):
        """Test confidence at threshold"""
        should_proceed, reason = self.guardrails.check_confidence_threshold(
            confidence=0.70,
            intent="update_address",
            threshold=0.70
        )
        
        assert should_proceed is True
    
    # ============= PII Sanitization Tests =============
    
    def test_sanitize_ssn(self):
        """Test SSN sanitization for logging"""
        text = "My SSN is 123-45-6789"
        sanitized = self.guardrails.sanitize_pii(text)
        
        assert "123-45-6789" not in sanitized
        assert "XXX-XX-XXXX" in sanitized
    
    def test_sanitize_credit_card(self):
        """Test credit card sanitization"""
        text = "Card: 4532-1234-5678-9010"
        sanitized = self.guardrails.sanitize_pii(text)
        
        assert "4532-1234-5678-9010" not in sanitized
        assert "XXXX-XXXX-XXXX-XXXX" in sanitized
    
    def test_sanitize_multiple_pii(self):
        """Test sanitization of multiple PII types"""
        text = "My SSN is 123-45-6789 and card is 4532-1234-5678-9010"
        sanitized = self.guardrails.sanitize_pii(text)
        
        assert "123-45-6789" not in sanitized
        assert "4532-1234-5678-9010" not in sanitized
        assert "XXX-XX-XXXX" in sanitized
        assert "XXXX-XXXX-XXXX-XXXX" in sanitized
    
    # ============= Violation Summary Tests =============
    
    def test_violation_summary_no_violations(self):
        """Test summary with no violations"""
        summary = self.guardrails.get_violation_summary([])
        assert "No violations" in summary
    
    def test_violation_summary_with_violations(self):
        """Test summary with multiple violations"""
        text = "My SSN is 123-45-6789 and this damn system is broken"
        _, violations = self.guardrails.validate_input(text, "CUST123")
        
        summary = self.guardrails.get_violation_summary(violations)
        assert "error" in summary.lower()
        assert "warning" in summary.lower()


class TestPromptBasedGuardrails:
    """Test prompt-based guardrail templates"""
    
    def test_system_prompt_contains_rules(self):
        """Test that system prompt has key guardrail rules"""
        assert "NEVER share" in SYSTEM_PROMPT_GUARDRAILS
        assert "NEVER make up" in SYSTEM_PROMPT_GUARDRAILS
        assert "ONLY discuss banking" in SYSTEM_PROMPT_GUARDRAILS
        assert "professionalism" in SYSTEM_PROMPT_GUARDRAILS.lower()
    
    def test_intent_specific_guardrails(self):
        """Test intent-specific guardrail prompts"""
        address_guardrails = get_guardrail_prompt("update_address")
        assert "address" in address_guardrails.lower()
        assert "verify" in address_guardrails.lower()
        
        fraud_guardrails = get_guardrail_prompt("report_fraud")
        assert "fraud" in fraud_guardrails.lower()
        assert "urgent" in fraud_guardrails.lower()
    
    def test_unknown_intent_fallback(self):
        """Test fallback guardrails for unknown intents"""
        guardrails = get_guardrail_prompt("some_random_intent")
        assert "unclear" in guardrails.lower() or "unknown" in guardrails.lower()


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def setup_method(self):
        self.guardrails = GuardrailService()
    
    def test_legitimate_address_update_with_phone(self):
        """Test address update that mentions phone for contact"""
        text = "Please update my address to 456 Oak St, Boston, MA 02101. You can reach me at 555-123-4567 if needed."
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        # Has PII (phone) but should still be processed with warning
        # Phone in context of contact is different from random PII
        assert any(v.rule == "pii_phone" for v in violations)
    
    def test_fraud_report_without_card_details(self):
        """Test fraud report that doesn't expose card numbers"""
        text = "I see unauthorized charges on my account - someone is using my card!"
        is_safe, violations = self.guardrails.validate_input(text, "CUST123")
        
        # Should be safe - no PII exposed
        assert is_safe is True
        assert not any("pii" in v.rule for v in violations)
    
    def test_response_with_acknowledgment_not_hallucination(self):
        """Test response with case number that's not a hallucination"""
        response = "I've created case #CASE-2024-001 for your request"
        user_input = "Report fraud"
        is_safe, violations = self.guardrails.validate_output(
            response, {"customer_id": "CUST123"}, user_input
        )
        
        # Short case numbers should be OK, not flagged as hallucination
        assert is_safe is True
