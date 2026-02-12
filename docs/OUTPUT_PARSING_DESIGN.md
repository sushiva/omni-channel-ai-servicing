# Structured Output Parsing Design

## Problem Statement

**Current State:** Manual string parsing of LLM outputs
```python
intent = response.strip().lower()  # Brittle, no validation
entities = json.loads(response)     # Can fail, no type safety
```

**Issues:**
- No type safety (strings instead of enums)
- No validation (invalid intents pass through)
- Manual parsing (error-prone)
- Difficult to test
- No retry logic when LLM returns bad format

---

## Solution: LangChain OutputParsers

### 1. Intent Classification (EnumOutputParser)

**Before:**
```python
response = "address_update"  # Just a string
```

**After:**
```python
from enum import Enum

class CustomerIntent(str, Enum):
    ADDRESS_UPDATE = "address_update"
    FRAUD_REPORT = "fraud_report"
    # ...

intent: CustomerIntent = parser.parse(response)  # Type-safe enum
```

### 2. Entity Extraction (PydanticOutputParser)

**Before:**
```python
entities = {"street": "123 Main St", "city": "Boston"}  # Just a dict
```

**After:**
```python
from pydantic import BaseModel, Field

class AddressEntity(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City name")
    state: str = Field(description="Two-letter state code")
    zip_code: str = Field(description="5-digit ZIP code")

entities: AddressEntity = parser.parse(response)  # Validated Pydantic model
```

---

## Implementation Plan

### Phase 1: Domain Models (Type Definitions)

**File:** `omni_channel_ai_servicing/domain/models/intent.py`
```python
from enum import Enum

class CustomerIntent(str, Enum):
    """All possible customer intents"""
    ADDRESS_UPDATE = "address_update"
    FRAUD_REPORT = "fraud_report"
    DISPUTE = "dispute"
    STATEMENT_REQUEST = "statement_request"
    ACCOUNT_INQUIRY = "account_inquiry"
    PAYMENT_ISSUE = "payment_issue"
    CARD_ACTIVATION = "card_activation"
    FALLBACK = "fallback"
```

**File:** `omni_channel_ai_servicing/domain/models/entities.py`
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class AddressEntity(BaseModel):
    street: str = Field(description="Street address with number")
    city: str = Field(description="City name")
    state: str = Field(description="Two-letter state code")
    zip_code: str = Field(description="5-digit ZIP code", pattern=r"^\d{5}$")
    
    @validator('state')
    def validate_state(cls, v):
        if len(v) != 2:
            raise ValueError("State must be 2 letters")
        return v.upper()

class DisputeEntity(BaseModel):
    transaction_id: Optional[str] = Field(description="Transaction ID if provided")
    amount: Optional[float] = Field(description="Disputed amount")
    date: Optional[str] = Field(description="Transaction date")
    merchant: Optional[str] = Field(description="Merchant name")
    reason: str = Field(description="Reason for dispute")
```

### Phase 2: Output Parsers

**File:** `omni_channel_ai_servicing/llm/output_parsers.py`
```python
from langchain.output_parsers import EnumOutputParser, PydanticOutputParser
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from omni_channel_ai_servicing.domain.models.entities import AddressEntity, DisputeEntity

# Intent parser
intent_parser = EnumOutputParser(enum=CustomerIntent)

# Entity parsers (intent-specific)
entity_parsers = {
    CustomerIntent.ADDRESS_UPDATE: PydanticOutputParser(pydantic_object=AddressEntity),
    CustomerIntent.DISPUTE: PydanticOutputParser(pydantic_object=DisputeEntity),
    # Add more as needed
}

def get_entity_parser(intent: CustomerIntent):
    """Get the appropriate entity parser for an intent"""
    return entity_parsers.get(intent, None)
```

### Phase 3: Update Intent Classifier

**File:** `omni_channel_ai_servicing/graph/nodes/classify_intent.py`

**Before:**
```python
def classify_intent_node(state: State) -> dict:
    response = llm.generate(prompt)
    intent = response.strip().lower()  # String
    return {"intent": intent}
```

**After:**
```python
from omni_channel_ai_servicing.llm.output_parsers import intent_parser
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent

def classify_intent_node(state: State) -> dict:
    # Add format instructions to prompt
    format_instructions = intent_parser.get_format_instructions()
    prompt = f"{INTENT_PROMPT}\n\n{format_instructions}"
    
    response = llm.generate(prompt)
    
    try:
        intent: CustomerIntent = intent_parser.parse(response)
    except Exception as e:
        logger.warning(f"Failed to parse intent: {e}")
        intent = CustomerIntent.FALLBACK
    
    return {"intent": intent.value}  # Store as string for compatibility
```

### Phase 4: Update Entity Extractor

**File:** `omni_channel_ai_servicing/graph/nodes/extract_entities.py`

**Before:**
```python
def extract_entities_node(state: State) -> dict:
    response = llm.generate(prompt)
    entities = json.loads(response)  # Dict
    return {"entities": entities}
```

**After:**
```python
from omni_channel_ai_servicing.llm.output_parsers import get_entity_parser
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent

def extract_entities_node(state: State) -> dict:
    intent = CustomerIntent(state["intent"])
    parser = get_entity_parser(intent)
    
    if not parser:
        # No structured parsing for this intent
        return {"entities": {}}
    
    format_instructions = parser.get_format_instructions()
    prompt = f"{ENTITY_PROMPT}\n\n{format_instructions}"
    
    response = llm.generate(prompt)
    
    try:
        entities = parser.parse(response)
        return {"entities": entities.dict()}
    except Exception as e:
        logger.warning(f"Failed to parse entities: {e}")
        return {"entities": {}}
```

---

## Benefits

### 1. Type Safety
```python
# Before: Could pass any string
workflow.invoke({"intent": "random_nonsense"})  # No error!

# After: Type-checked at parse time
intent = CustomerIntent.ADDRESS_UPDATE  # IDE autocomplete
```

### 2. Validation
```python
# Before: Invalid data slips through
{"state": "California"}  # Should be "CA"

# After: Pydantic validates
AddressEntity(state="California")  # Raises ValidationError
AddressEntity(state="CA")          # ✓ Normalized to uppercase
```

### 3. Better Prompts
```python
# OutputParser adds format instructions automatically:
"""
You must respond with one of: address_update, fraud_report, dispute
Your response must be exactly one of these values.
"""
```

### 4. Retry Logic (Future Enhancement)
```python
from langchain.output_parsers import RetryWithErrorOutputParser

retry_parser = RetryWithErrorOutputParser.from_llm(
    parser=intent_parser,
    llm=llm
)
# Automatically retries with error feedback if parse fails
```

---

## Testing Strategy

### Unit Tests
```python
def test_intent_parser_valid():
    result = intent_parser.parse("address_update")
    assert result == CustomerIntent.ADDRESS_UPDATE
    assert isinstance(result, CustomerIntent)

def test_intent_parser_invalid():
    with pytest.raises(ValueError):
        intent_parser.parse("invalid_intent")

def test_address_entity_validation():
    entity = AddressEntity(
        street="123 Main St",
        city="Boston",
        state="ma",  # Lowercase
        zip_code="02101"
    )
    assert entity.state == "MA"  # Auto-uppercased
```

### Integration Tests
```python
def test_intent_classification_with_parser():
    state = {"message": "I need to update my address"}
    result = classify_intent_node(state)
    assert isinstance(result["intent"], str)  # Still compatible
    assert result["intent"] == "address_update"
```

---

## Migration Path

### Phase 1: Add parsers alongside existing code ✅
- No breaking changes
- Both approaches work

### Phase 2: Update nodes to use parsers ✅
- Backward compatible (store enum.value as string)

### Phase 3: Update downstream code to use enums
- Gradually replace string comparisons
- `if intent == "address_update"` → `if intent == CustomerIntent.ADDRESS_UPDATE`

### Phase 4: Remove old parsing code
- Clean up manual parsing
- Full type safety

---

## Interview Talking Points

**"Why did you add OutputParsers?"**
- "Manual string parsing was brittle and error-prone"
- "Wanted type safety and validation"
- "LangChain provides built-in retry logic"
- "Easier to test and maintain"

**"What challenges did you face?"**
- "Backward compatibility - had to store enum values as strings"
- "Balance between structure and flexibility"
- "Some intents don't need structured entities"

**"How does this scale?"**
- "Easy to add new intents - just extend the enum"
- "Pydantic models are self-documenting"
- "Can add validators for complex business rules"

---

## Future Enhancements

1. **Retry Logic**: Add `RetryWithErrorOutputParser`
2. **Streaming**: Parse partial responses
3. **Multi-format**: Support JSON and YAML outputs
4. **Custom Validators**: Business rule validation in Pydantic
5. **Metrics**: Track parsing failures
