# Guardrails System Design

## What We Need

### Business Requirements
1. **Safety**: Prevent disclosure of sensitive customer data (PII, account numbers)
2. **Accuracy**: Prevent LLM hallucinations (fake policy numbers, made-up information)
3. **Compliance**: Ensure responses follow banking regulations and policies
4. **Relevance**: Keep conversations on-topic (banking services only)
5. **Quality**: Route low-confidence requests to human agents

### Technical Requirements
1. Validate user inputs before LLM processing
2. Validate LLM outputs before sending to customers
3. Support both programmatic and prompt-based guardrails
4. Provide confidence thresholds for human escalation
5. Sanitize PII for logging/monitoring
6. Track guardrail violations for metrics

---

## Architecture

### High-Level Flow

```
User Input
    ↓
┌─────────────────────────┐
│ Input Guardrails        │
│ - PII detection         │
│ - Profanity check       │
│ - Injection attempts    │
│ - Topic relevance       │
└─────────────────────────┘
    ↓ (if safe)
┌─────────────────────────┐
│ LLM Processing          │
│ (with prompt guardrails)│
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ Output Guardrails       │
│ - PII leakage           │
│ - Hallucinations        │
│ - Response quality      │
│ - Relevance check       │
└─────────────────────────┘
    ↓ (if safe)
Send to Customer
```

### Two-Layer Approach

**Layer 1: Prompt-Based Guardrails (Soft)**
- Embedded in system prompts
- Instructs LLM on safety rules
- Fast, no extra processing
- ⚠️ Can be bypassed by adversarial prompts

**Layer 2: Programmatic Guardrails (Hard)**
- Code-based validation
- Uses regex, pattern matching, rules
- Cannot be bypassed
- ✅ Deterministic enforcement

---

## Components

### 1. GuardrailService (Core)

**Purpose**: Central service for all validation logic

**Key Methods**:
```python
validate_input(text, customer_id) → (is_safe, violations)
validate_output(response, context, user_input) → (is_safe, violations)
check_confidence_threshold(confidence, intent) → (should_proceed, reason)
sanitize_pii(text) → sanitized_text
```

**Validation Rules**:

| Rule Type | Severity | Action |
|-----------|----------|--------|
| PII (SSN, credit card) | ERROR | Block |
| SQL injection | ERROR | Block |
| Hallucinations | ERROR | Block |
| Profanity | WARNING | Log, proceed |
| Off-topic | WARNING | Log, proceed |
| Short response | WARNING | Log, proceed |

### 2. Prompt-Based Guardrails

**System Prompt Template**:
```
CRITICAL SAFETY RULES:
1. NEVER share: SSN, account numbers, passwords
2. NEVER make up: policy numbers, dates, amounts
3. ONLY discuss banking topics
4. If uncertain, escalate to human
```

**Intent-Specific Guardrails**:
- Address updates: Verify identity, confirm changes
- Fraud reports: Urgent handling, no card number requests
- Statements: Verify delivery method

### 3. Integration Points

**Email Processor**:
```python
# Before processing
is_safe, violations = processor.validate_email_content(cleaned_body, customer_id)
if not is_safe:
    return "Please contact us at 1-800-BANK for assistance"
```

**LLM Nodes** (classify_intent, extract_entities):
```python
# Inject guardrails into prompts
prompt = INTENT_PROMPT.format(
    message=user_message,
    guardrails=SYSTEM_PROMPT_GUARDRAILS
)
```

**API Layer**:
```python
# After LLM response
is_safe, violations = guardrails.validate_output(response, context, user_input)
if not is_safe:
    response = "Let me connect you with a specialist"
```

---

## Validation Patterns

### PII Detection

**Regex Patterns**:
- SSN: `\b\d{3}-\d{2}-\d{4}\b`
- Credit Card: `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b`
- Phone: `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`

**Production Enhancement**: Use NER models (spaCy, transformers) for better accuracy

### Hallucination Detection

**Pattern Matching**:
- Fake policy: `policy\s+#?\d{10,}` (unrealistically long)
- Fake account: `account\s+#?\d{15,}` (unrealistically long)
- Fake transaction: `transaction\s+id:?\s*[A-Z0-9]{20,}` (unrealistically long)

**Production Enhancement**: Validate against CRM/database, use confidence scores

### Injection Prevention

**SQL Patterns**:
- `union\s+select`
- `drop\s+table`
- `insert\s+into`
- `exec\s*\(`

**Production Enhancement**: Input sanitization, parameterized queries

---

## Confidence Thresholds

### Decision Matrix

| Confidence | Action | Rationale |
|------------|--------|-----------|
| ≥ 0.90 | Fully automated | High certainty |
| 0.70 - 0.89 | Automated with logging | Monitor for drift |
| 0.50 - 0.69 | Route to human | Medium uncertainty |
| < 0.50 | Immediate human escalation | Low certainty |

### Intent-Specific Thresholds

**High-risk intents** (fraud, disputes): Higher threshold (0.80)
**Low-risk intents** (address, statement): Standard threshold (0.70)

---

## Metrics & Monitoring

### Key Metrics

**Guardrail Violations**:
- `guardrail_violations_total{rule, severity}`
- `guardrail_blocked_requests_total{rule}`

**Confidence Distribution**:
- `intent_confidence_histogram{intent}`
- `low_confidence_escalations_total{intent}`

**Safety Events**:
- `pii_detected_total{type, location}` (location = input/output)
- `hallucination_detected_total{type}`

---

## Testing Strategy

### Unit Tests

1. **Input Validation**: Clean requests, PII detection, injection attempts
2. **Output Validation**: Clean responses, hallucinations, PII leakage
3. **Confidence Checks**: Threshold boundaries
4. **PII Sanitization**: Redaction accuracy
5. **Edge Cases**: Multiple violations, borderline cases

### Integration Tests

1. **End-to-End**: User input → guardrails → LLM → guardrails → response
2. **Prompt Injection**: Adversarial prompts attempting to bypass guardrails
3. **Performance**: Validation latency (< 50ms target)

### Production Monitoring

1. **Violation Rates**: Track trends over time
2. **False Positives**: Legitimate requests blocked
3. **False Negatives**: Unsafe content getting through (manual review sample)

---

## Implementation Plan

### Phase 1: Core Guardrails ✅
- [x] GuardrailService class with validation methods
- [x] PII detection patterns
- [x] Hallucination detection
- [x] Confidence thresholds

### Phase 2: Prompt Integration ✅
- [x] System prompt template with safety rules
- [x] Intent-specific guardrails
- [x] Inject into intent classifier
- [x] Inject into entity extractor

### Phase 3: Service Integration ✅
- [x] Email processor validation
- [x] API layer validation
- [x] Error handling and fallback responses

### Phase 4: Testing (Current)
- [x] Unit tests for all validation rules
- [ ] Run tests and verify coverage
- [ ] Integration tests with real workflows

### Phase 5: Metrics (Next)
- [ ] Add guardrail metrics to MetricsCollector
- [ ] Track violations by type
- [ ] Dashboard for guardrail monitoring

---

## Interview Talking Points

### Architecture Decision: Two-Layer Approach

**Why both prompt-based AND programmatic?**
- **Defense in depth**: Multiple layers of protection
- **Flexibility**: Prompt-based can adapt to context
- **Reliability**: Programmatic ensures enforcement
- **Performance**: Prompt-based is "free" (no extra latency)

### Handling Trade-offs

**False Positives vs False Negatives**:
- Bias toward false positives (safer)
- Low-risk violations = warnings (log but proceed)
- High-risk violations = errors (block immediately)

**Latency vs Safety**:
- Regex validation: < 5ms
- Production: Could use async validation for non-blocking
- Critical path: Input validation only (output validated before send)

### Scalability

**Pattern-based → ML-based**:
- Start: Simple regex patterns (fast, interpretable)
- Scale: NER models for PII (spaCy, transformers)
- Future: Dedicated guardrail models (LlamaGuard, Guardrails AI)

**Centralized Service**:
- All validation logic in one place
- Easy to update rules
- Consistent enforcement across channels

---

## Production Enhancements

### Short-term (Next Sprint)
1. **Metrics Integration**: Track all guardrail events
2. **Logging**: Structured logs for violations
3. **Confidence Tuning**: A/B test thresholds

### Medium-term (Next Quarter)
1. **ML-based PII Detection**: Replace regex with NER models
2. **Semantic Similarity**: Check response relevance vs input
3. **User Feedback Loop**: Learn from escalations

### Long-term (Future)
1. **Dedicated Guardrail Models**: Fine-tuned LLMs for safety
2. **Real-time Policy Updates**: Dynamic rule loading
3. **Multi-language Support**: Non-English guardrails
