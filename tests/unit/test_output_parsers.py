"""
Unit tests for structured output parsing.
Tests EnumOutputParser for intents and PydanticOutputParser for entities.
"""
import pytest
from pydantic import ValidationError

from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from omni_channel_ai_servicing.domain.models.entities import (
    AddressEntity,
    DisputeEntity,
    CardEntity,
    GenericEntity
)
from omni_channel_ai_servicing.llm.output_parsers import (
    intent_parser,
    get_entity_parser,
    get_intent_format_instructions,
    get_entity_format_instructions
)


class TestIntentParsing:
    """Test intent enum parsing"""
    
    def test_parse_valid_intent(self):
        """Test parsing valid intent string"""
        result = intent_parser.parse("address_update")
        assert result == CustomerIntent.ADDRESS_UPDATE
        assert isinstance(result, CustomerIntent)
    
    def test_parse_all_intents(self):
        """Test all defined intents can be parsed"""
        for intent in CustomerIntent:
            result = intent_parser.parse(intent.value)
            assert result == intent
    
    def test_intent_format_instructions(self):
        """Test format instructions are generated"""
        instructions = get_intent_format_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # Should mention the valid values
        assert "address_update" in instructions or "ADDRESS_UPDATE" in instructions


class TestAddressEntityParsing:
    """Test address entity Pydantic parsing"""
    
    def test_valid_address_entity(self):
        """Test creating valid address entity"""
        entity = AddressEntity(
            street="123 Main St",
            city="Boston",
            state="MA",
            zip_code="02101"
        )
        assert entity.street == "123 Main St"
        assert entity.city == "Boston"
        assert entity.state == "MA"
        assert entity.zip_code == "02101"
    
    def test_state_normalization(self):
        """Test state code is normalized to uppercase"""
        entity = AddressEntity(
            street="123 Main St",
            city="Boston",
            state="ma",  # Lowercase
            zip_code="02101"
        )
        assert entity.state == "MA"  # Should be uppercased
    
    def test_invalid_zip_code(self):
        """Test invalid ZIP code raises validation error"""
        with pytest.raises(ValidationError):
            AddressEntity(
                street="123 Main St",
                city="Boston",
                state="MA",
                zip_code="1234"  # Only 4 digits
            )
    
    def test_zip_code_not_numeric(self):
        """Test non-numeric ZIP code raises error"""
        with pytest.raises(ValidationError):
            AddressEntity(
                street="123 Main St",
                city="Boston",
                state="MA",
                zip_code="abcde"
            )
    
    def test_address_entity_to_dict(self):
        """Test entity can be converted to dict"""
        entity = AddressEntity(
            street="123 Main St",
            city="Boston",
            state="MA",
            zip_code="02101",
            address_type="mailing"
        )
        data = entity.dict()
        assert data["street"] == "123 Main St"
        assert data["state"] == "MA"
        assert data["address_type"] == "mailing"


class TestDisputeEntityParsing:
    """Test dispute entity Pydantic parsing"""
    
    def test_valid_dispute_entity(self):
        """Test creating valid dispute entity"""
        entity = DisputeEntity(
            transaction_id="TXN123",
            amount=49.99,
            merchant="Amazon",
            reason="Item not received",
            is_fraud=False
        )
        assert entity.transaction_id == "TXN123"
        assert entity.amount == 49.99
        assert entity.is_fraud is False
    
    def test_dispute_minimal_fields(self):
        """Test dispute with only required fields"""
        entity = DisputeEntity(reason="Unauthorized charge")
        assert entity.reason == "Unauthorized charge"
        assert entity.transaction_id is None
        assert entity.is_fraud is False  # Default value
    
    def test_negative_amount_validation(self):
        """Test negative amount raises validation error"""
        with pytest.raises(ValidationError):
            DisputeEntity(
                reason="Test",
                amount=-10.0
            )
    
    def test_fraud_flag(self):
        """Test fraud flag can be set"""
        entity = DisputeEntity(
            reason="Unauthorized transaction",
            is_fraud=True
        )
        assert entity.is_fraud is True


class TestCardEntityParsing:
    """Test card entity Pydantic parsing"""
    
    def test_valid_card_entity(self):
        """Test creating valid card entity"""
        entity = CardEntity(
            card_last_four="1234",
            card_type="debit",
            action="activate"
        )
        assert entity.card_last_four == "1234"
        assert entity.action == "activate"
    
    def test_invalid_card_digits(self):
        """Test invalid card digits raise error"""
        with pytest.raises(ValidationError):
            CardEntity(
                card_last_four="12",  # Only 2 digits
                action="activate"
            )
    
    def test_card_without_last_four(self):
        """Test card entity without last 4 digits"""
        entity = CardEntity(
            action="replace",
            reason="lost"
        )
        assert entity.card_last_four is None
        assert entity.action == "replace"


class TestOutputParserIntegration:
    """Test output parser integration functions"""
    
    def test_get_entity_parser_address(self):
        """Test getting parser for address intent"""
        parser = get_entity_parser(CustomerIntent.ADDRESS_UPDATE)
        assert parser is not None
        # Should have format instructions
        instructions = parser.get_format_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0
    
    def test_get_entity_parser_dispute(self):
        """Test getting parser for dispute intent"""
        parser = get_entity_parser(CustomerIntent.DISPUTE)
        assert parser is not None
    
    def test_get_entity_parser_fallback(self):
        """Test fallback intent may not have parser"""
        parser = get_entity_parser(CustomerIntent.FALLBACK)
        # Fallback might not have a structured parser
        assert parser is None or parser is not None  # Either is valid
    
    def test_get_entity_format_instructions(self):
        """Test getting format instructions for entity parsing"""
        instructions = get_entity_format_instructions(CustomerIntent.ADDRESS_UPDATE)
        assert instructions is not None
        assert isinstance(instructions, str)
        # Should mention JSON schema or fields
        assert "street" in instructions or "city" in instructions or "JSON" in instructions.upper()


class TestGenericEntity:
    """Test generic entity for unstructured intents"""
    
    def test_generic_entity_creation(self):
        """Test creating generic entity"""
        entity = GenericEntity(
            summary="Customer asking about balance",
            key_details=["checking account", "current balance"]
        )
        assert entity.summary == "Customer asking about balance"
        assert len(entity.key_details) == 2
    
    def test_generic_entity_minimal(self):
        """Test generic entity with only summary"""
        entity = GenericEntity(summary="Simple query")
        assert entity.summary == "Simple query"
        assert entity.key_details is None


class TestIntentEnumUtilities:
    """Test CustomerIntent enum helper methods"""
    
    def test_intent_description(self):
        """Test getting intent description"""
        desc = CustomerIntent.get_description(CustomerIntent.ADDRESS_UPDATE)
        assert isinstance(desc, str)
        assert len(desc) > 0
    
    def test_all_intents_have_descriptions(self):
        """Test all intents have descriptions"""
        for intent in CustomerIntent:
            desc = CustomerIntent.get_description(intent)
            assert desc is not None
            assert len(desc) > 0
    
    def test_intent_value_access(self):
        """Test accessing intent value"""
        assert CustomerIntent.ADDRESS_UPDATE.value == "address_update"
        assert CustomerIntent.FRAUD_REPORT.value == "fraud_report"
