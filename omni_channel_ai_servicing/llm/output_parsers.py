"""
LangChain output parsers for structured LLM responses.

Provides type-safe parsing of LLM outputs into domain models:
- Custom EnumOutputParser for intent classification
- PydanticOutputParser for entity extraction
"""
from langchain_core.output_parsers import PydanticOutputParser, BaseOutputParser
from typing import Dict, Optional
from enum import Enum
from pydantic import Field

from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from omni_channel_ai_servicing.domain.models.entities import (
    AddressEntity,
    DisputeEntity,
    StatementEntity,
    PaymentEntity,
    CardEntity,
    GenericEntity
)


class EnumOutputParser(BaseOutputParser[Enum]):
    """
    Custom parser for enum values.
    Parses LLM output into a Python Enum.
    """
    
    enum: type[Enum] = Field(..., description="The enum class to parse into")
    
    enum: type[Enum]
    
    def parse(self, text: str) -> Enum:
        """Parse text into enum value"""
        text = text.strip().lower()
        
        # Try direct value match
        for member in self.enum:
            if member.value.lower() == text:
                return member
        
        # Try name match
        for member in self.enum:
            if member.name.lower() == text:
                return member
        
        # If no match, raise error
        valid_values = [m.value for m in self.enum]
        raise ValueError(f"Invalid value '{text}'. Must be one of: {valid_values}")
    
    def get_format_instructions(self) -> str:
        """Get format instructions for the LLM"""
        values = [member.value for member in self.enum]
        return f"""You must respond with exactly one of these values (case-insensitive):
{', '.join(values)}

Do not include any explanation or additional text. Only output the exact value."""


# Intent Classification Parser
intent_parser = EnumOutputParser(enum=CustomerIntent)
from omni_channel_ai_servicing.domain.models.entities import (
    AddressEntity,
    DisputeEntity,
    StatementEntity,
    PaymentEntity,
    CardEntity,
    GenericEntity
)


# Intent Classification Parser
intent_parser = EnumOutputParser(enum=CustomerIntent)


# Entity Parsers (intent-specific)
_entity_parsers: Dict[CustomerIntent, PydanticOutputParser] = {
    CustomerIntent.ADDRESS_UPDATE: PydanticOutputParser(pydantic_object=AddressEntity),
    CustomerIntent.DISPUTE: PydanticOutputParser(pydantic_object=DisputeEntity),
    CustomerIntent.FRAUD_REPORT: PydanticOutputParser(pydantic_object=DisputeEntity),
    CustomerIntent.STATEMENT_REQUEST: PydanticOutputParser(pydantic_object=StatementEntity),
    CustomerIntent.PAYMENT_ISSUE: PydanticOutputParser(pydantic_object=PaymentEntity),
    CustomerIntent.CARD_ACTIVATION: PydanticOutputParser(pydantic_object=CardEntity),
    CustomerIntent.CARD_REPLACEMENT: PydanticOutputParser(pydantic_object=CardEntity),
    CustomerIntent.ACCOUNT_INQUIRY: PydanticOutputParser(pydantic_object=GenericEntity),
    CustomerIntent.BALANCE_INQUIRY: PydanticOutputParser(pydantic_object=GenericEntity),
}


def get_entity_parser(intent: CustomerIntent) -> Optional[PydanticOutputParser]:
    """
    Get the appropriate Pydantic parser for a given intent.
    
    Args:
        intent: The classified customer intent
        
    Returns:
        PydanticOutputParser instance for the intent, or None if no structured parsing needed
        
    Examples:
        >>> parser = get_entity_parser(CustomerIntent.ADDRESS_UPDATE)
        >>> parser.get_format_instructions()
        'The output should be formatted as a JSON instance that conforms to...'
    """
    return _entity_parsers.get(intent)


def get_intent_format_instructions() -> str:
    """
    Get format instructions for intent classification.
    
    Returns:
        String containing instructions for the LLM on how to format intent responses
    """
    return intent_parser.get_format_instructions()


def get_entity_format_instructions(intent: CustomerIntent) -> Optional[str]:
    """
    Get format instructions for entity extraction based on intent.
    
    Args:
        intent: The classified customer intent
        
    Returns:
        String containing instructions for the LLM, or None if no parser exists
    """
    parser = get_entity_parser(intent)
    return parser.get_format_instructions() if parser else None


# Export convenience functions
__all__ = [
    'intent_parser',
    'get_entity_parser',
    'get_intent_format_instructions',
    'get_entity_format_instructions',
    'CustomerIntent',
    'AddressEntity',
    'DisputeEntity',
    'StatementEntity',
    'PaymentEntity',
    'CardEntity',
    'GenericEntity',
]
