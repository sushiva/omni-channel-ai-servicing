"""
Guardrails service for validating LLM inputs and outputs.

Implements both programmatic validation and provides prompt-based guardrail templates.
Ensures safe, compliant, and accurate AI responses.
"""

import re
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""
    rule: str
    severity: str  # "error", "warning"
    message: str
    detected_content: Optional[str] = None


class GuardrailService:
    """
    Service for validating inputs and outputs against safety rules.
    
    Implements multiple layers of protection:
    1. Input validation (before LLM)
    2. Output validation (after LLM)
    3. Content safety checks
    4. Compliance validation
    """
    
    # PII patterns (simple regex, production would use NER models)
    PII_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "email_in_content": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }
    
    # Profanity/inappropriate content (basic list)
    PROFANITY_LIST = [
        "damn", "hell", "shit", "fuck", "bitch", "bastard", "asshole"
    ]
    
    # SQL injection patterns (raw strings for compilation)
    INJECTION_PATTERN_STRINGS = [
        r"(?i)(union\s+select)",
        r"(?i)(drop\s+table)",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(exec\s*\()",
        r"(?i)(script\s*>)",
    ]
    
    # Banking-specific hallucination patterns (raw strings)
    HALLUCINATION_PATTERN_STRINGS = {
        "fake_policy": r"(?i)policy\s+#?\d{10,}",
        "fake_account": r"(?i)account\s+#?\d{15,}",
        "fake_transaction": r"(?i)transaction\s+id:?\s*[A-Z0-9]{20,}",
    }
    
    def __init__(self):
        self.violations: List[GuardrailViolation] = []
        
        # Pre-compile all regex patterns for performance
        self._compiled_pii_patterns = {
            name: re.compile(pattern) 
            for name, pattern in self.PII_PATTERNS.items()
        }
        self._compiled_injection_patterns = [
            re.compile(pattern) 
            for pattern in self.INJECTION_PATTERN_STRINGS
        ]
        self._compiled_hallucination_patterns = {
            name: re.compile(pattern)
            for name, pattern in self.HALLUCINATION_PATTERN_STRINGS.items()
        }
    
    # ============= Input Guardrails (Before LLM) =============
    
    def validate_input(self, text: str, customer_id: str) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Validate user input before sending to LLM.
        
        Checks for:
        - PII in user message
        - Profanity/inappropriate content
        - Injection attacks
        - Off-topic requests
        
        Args:
            text: User input text
            customer_id: Customer identifier
            
        Returns:
            (is_safe, violations) - is_safe=False means block the request
        """
        violations = []
        
        # Check for PII leakage
        pii_violations = self._check_pii(text)
        violations.extend(pii_violations)
        
        # Check for profanity
        profanity_violations = self._check_profanity(text)
        violations.extend(profanity_violations)
        
        # Check for injection attempts
        injection_violations = self._check_injection(text)
        violations.extend(injection_violations)
        
        # Check if request is banking-related
        topic_violations = self._check_topic_relevance(text)
        violations.extend(topic_violations)
        
        # Determine if safe (no "error" severity violations)
        is_safe = not any(v.severity == "error" for v in violations)
        
        return is_safe, violations
    
    # ============= Output Guardrails (After LLM) =============
    
    def validate_output(
        self, 
        response: str, 
        context: Dict,
        user_input: str
    ) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Validate LLM output before sending to customer.
        
        Checks for:
        - PII disclosure
        - Hallucinations (fake account numbers, policies)
        - Off-topic responses
        - Professionalism
        - Accuracy vs context
        
        Args:
            response: LLM generated response
            context: Request context (customer_id, intent, etc.)
            user_input: Original user request
            
        Returns:
            (is_safe, violations) - is_safe=False means block the response
        """
        violations = []
        
        # Check for PII leakage in response
        pii_violations = self._check_pii(response)
        violations.extend(pii_violations)
        
        # Check for hallucinations
        hallucination_violations = self._check_hallucinations(response)
        violations.extend(hallucination_violations)
        
        # Check for profanity in LLM response
        profanity_violations = self._check_profanity(response)
        violations.extend(profanity_violations)
        
        # Check response relevance to input
        relevance_violations = self._check_response_relevance(response, user_input)
        violations.extend(relevance_violations)
        
        # Determine if safe
        is_safe = not any(v.severity == "error" for v in violations)
        
        return is_safe, violations
    
    # ============= Specific Validation Methods =============
    
    def _check_pii(self, text: str) -> List[GuardrailViolation]:
        """Check for PII patterns in text"""
        violations = []
        
        for pii_type, compiled_pattern in self._compiled_pii_patterns.items():
            matches = compiled_pattern.findall(text)
            if matches:
                violations.append(GuardrailViolation(
                    rule=f"pii_{pii_type}",
                    severity="error",
                    message=f"Detected {pii_type.replace('_', ' ')} in text",
                    detected_content=matches[0] if matches else None
                ))
        
        return violations
    
    def _check_profanity(self, text: str) -> List[GuardrailViolation]:
        """Check for profanity/inappropriate content"""
        violations = []
        text_lower = text.lower()
        
        for word in self.PROFANITY_LIST:
            if re.search(r'\b' + word + r'\b', text_lower):
                violations.append(GuardrailViolation(
                    rule="profanity",
                    severity="warning",
                    message=f"Detected inappropriate language",
                    detected_content=word
                ))
        
        return violations
    
    def _check_injection(self, text: str) -> List[GuardrailViolation]:
        """Check for SQL/script injection attempts"""
        violations = []
        
        for compiled_pattern in self._compiled_injection_patterns:
            if compiled_pattern.search(text):
                violations.append(GuardrailViolation(
                    rule="injection_attempt",
                    severity="error",
                    message="Detected potential injection attack",
                    detected_content=compiled_pattern.pattern
                ))
        
        return violations
    
    def _check_topic_relevance(self, text: str) -> List[GuardrailViolation]:
        """Check if request is banking/financial services related"""
        violations = []
        
        # Banking-related keywords
        banking_keywords = [
            "account", "address", "fraud", "transaction", "statement",
            "balance", "transfer", "payment", "card", "loan", "deposit",
            "withdrawal", "dispute", "credit", "debit", "bank"
        ]
        
        text_lower = text.lower()
        has_banking_keyword = any(keyword in text_lower for keyword in banking_keywords)
        
        # Non-banking topics that should be rejected
        off_topic_keywords = [
            "weather", "sports", "recipe", "movie", "game", "joke",
            "stock market", "investment advice", "tax advice"
        ]
        
        has_off_topic = any(keyword in text_lower for keyword in off_topic_keywords)
        
        if has_off_topic or (len(text) > 50 and not has_banking_keyword):
            violations.append(GuardrailViolation(
                rule="off_topic",
                severity="warning",
                message="Request appears to be off-topic for banking services"
            ))
        
        return violations
    
    def _check_hallucinations(self, response: str) -> List[GuardrailViolation]:
        """Check for likely hallucinations (fake numbers, policies)"""
        violations = []
        
        for hallucination_type, compiled_pattern in self._compiled_hallucination_patterns.items():
            matches = compiled_pattern.findall(response)
            if matches:
                violations.append(GuardrailViolation(
                    rule=f"hallucination_{hallucination_type}",
                    severity="error",
                    message=f"Detected potential hallucination: {hallucination_type.replace('_', ' ')}",
                    detected_content=matches[0] if matches else None
                ))
        
        return violations
    
    def _check_response_relevance(self, response: str, user_input: str) -> List[GuardrailViolation]:
        """Check if response is relevant to user input"""
        violations = []
        
        # Simple heuristic: response should be at least somewhat related
        # In production, use semantic similarity or LLM-based validation
        
        # Check response length
        if len(response) < 20:
            violations.append(GuardrailViolation(
                rule="response_too_short",
                severity="warning",
                message="Response seems too short to be helpful"
            ))
        
        # Check if response is generic/template
        generic_phrases = [
            "i don't know",
            "i'm not sure",
            "i cannot help",
            "i don't have that information"
        ]
        
        response_lower = response.lower()
        if any(phrase in response_lower for phrase in generic_phrases):
            violations.append(GuardrailViolation(
                rule="generic_response",
                severity="warning",
                message="Response appears to be a generic fallback"
            ))
        
        return violations
    
    # ============= Confidence-based Guardrails =============
    
    def check_confidence_threshold(
        self, 
        confidence: float, 
        intent: str,
        threshold: float = 0.7
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if confidence is above threshold for autonomous handling.
        
        Args:
            confidence: Confidence score (0-1)
            intent: Classified intent
            threshold: Minimum confidence required
            
        Returns:
            (should_proceed, reason) - should_proceed=False means route to human
        """
        if confidence < threshold:
            return False, f"Low confidence ({confidence:.2f}) for intent '{intent}' - routing to human agent"
        
        return True, None
    
    # ============= Utility Methods =============
    
    def sanitize_pii(self, text: str) -> str:
        """
        Redact PII from text for logging/monitoring.
        
        Args:
            text: Text potentially containing PII
            
        Returns:
            Text with PII redacted
        """
        sanitized = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == "ssn":
                sanitized = re.sub(pattern, "XXX-XX-XXXX", sanitized)
            elif pii_type == "credit_card":
                sanitized = re.sub(pattern, "XXXX-XXXX-XXXX-XXXX", sanitized)
            elif pii_type == "phone":
                sanitized = re.sub(pattern, "XXX-XXX-XXXX", sanitized)
            elif pii_type == "email_in_content":
                sanitized = re.sub(pattern, "[EMAIL_REDACTED]", sanitized)
        
        return sanitized
    
    def get_violation_summary(self, violations: List[GuardrailViolation]) -> str:
        """Get human-readable summary of violations"""
        if not violations:
            return "No violations detected"
        
        error_count = sum(1 for v in violations if v.severity == "error")
        warning_count = sum(1 for v in violations if v.severity == "warning")
        
        summary = f"Detected {error_count} error(s) and {warning_count} warning(s):\n"
        for v in violations:
            summary += f"  [{v.severity.upper()}] {v.rule}: {v.message}\n"
        
        return summary


# ============= Prompt-Based Guardrails =============

SYSTEM_PROMPT_GUARDRAILS = """
You are a banking customer service AI assistant.

CRITICAL SAFETY RULES - YOU MUST FOLLOW THESE:

1. NEVER share or discuss:
   - Account numbers
   - Social Security Numbers (SSN)
   - Credit card numbers
   - Passwords or PINs
   - Customer personal details beyond what they provide

2. NEVER make up or hallucinate:
   - Policy numbers
   - Account numbers
   - Transaction IDs
   - Dates or amounts
   - Bank procedures or policies

3. ONLY discuss banking topics:
   - Address updates
   - Fraud reports
   - Statement requests
   - General account inquiries
   - Transaction disputes

4. If asked about topics outside banking:
   - Politely decline: "I can only assist with banking-related requests."
   - Suggest contacting appropriate department

5. If you're uncertain or don't have information:
   - Say: "Let me connect you with a specialist who can help."
   - NEVER guess or make up information

6. Maintain professionalism:
   - Be courteous and helpful
   - Use clear, simple language
   - Stay calm even if customer is frustrated

7. Compliance:
   - Follow all banking regulations
   - Protect customer privacy
   - Document all interactions

If ANY rule is violated, stop and ask for human agent assistance.
"""


def get_guardrail_prompt(intent: str) -> str:
    """
    Get intent-specific guardrail instructions to add to prompts.
    
    Args:
        intent: The classified intent (e.g., "update_address", "report_fraud")
        
    Returns:
        Additional guardrail instructions for this specific intent
    """
    intent_guardrails = {
        "update_address": """
For address updates:
- Verify customer identity is confirmed before processing
- Ask for complete new address if not provided
- Confirm the change with customer before executing
- Never use example addresses or make up addresses
""",
        "report_fraud": """
For fraud reports:
- Take the report seriously and urgently
- Do NOT ask customer to share compromised card numbers
- Focus on getting description of fraudulent activity
- Assure immediate escalation to fraud team
- Never minimize customer's concerns
""",
        "request_statement": """
For statement requests:
- Confirm the statement period requested
- Verify delivery method (email, mail, portal)
- Do not discuss specific transaction amounts from memory
- Offer to escalate if they need specific transaction details
""",
        "unknown": """
For unclear requests:
- Ask clarifying questions politely
- Suggest common banking services
- If still unclear after 2 attempts, offer human agent
"""
    }
    
    return intent_guardrails.get(intent, intent_guardrails["unknown"])
