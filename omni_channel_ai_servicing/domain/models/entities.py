"""
Domain models for extracted entities from customer requests.
Pydantic models provide validation and type safety for entity extraction.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date


class AddressEntity(BaseModel):
    """Extracted address information from customer request"""
    
    street: str = Field(
        description="Street address including number and street name",
        examples=["123 Main Street", "456 Oak Avenue Apt 2B"]
    )
    city: str = Field(
        description="City name",
        examples=["Boston", "San Francisco"]
    )
    state: str = Field(
        description="Two-letter state code",
        min_length=2,
        max_length=2,
        examples=["MA", "CA", "NY"]
    )
    zip_code: str = Field(
        description="5-digit ZIP code",
        pattern=r"^\d{5}$",
        examples=["02101", "94102"]
    )
    address_type: Optional[str] = Field(
        default="mailing",
        description="Type of address: mailing, billing, or both",
        examples=["mailing", "billing", "both"]
    )
    
    @validator('state')
    def normalize_state(cls, v):
        """Normalize state to uppercase"""
        if not v:
            raise ValueError("State is required")
        return v.upper()
    
    @validator('zip_code')
    def validate_zip(cls, v):
        """Validate ZIP code format"""
        if not v or not v.isdigit() or len(v) != 5:
            raise ValueError("ZIP code must be 5 digits")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "address_type": "mailing"
            }
        }


class DisputeEntity(BaseModel):
    """Extracted dispute/fraud information from customer request"""
    
    transaction_id: Optional[str] = Field(
        default=None,
        description="Transaction ID or reference number if provided",
        examples=["TXN123456", "REF-2024-001"]
    )
    amount: Optional[float] = Field(
        default=None,
        description="Disputed or fraudulent amount in dollars",
        examples=[49.99, 1250.00]
    )
    transaction_date: Optional[str] = Field(
        default=None,
        description="Date of the transaction (YYYY-MM-DD format)",
        examples=["2024-02-10", "2024-01-15"]
    )
    merchant: Optional[str] = Field(
        default=None,
        description="Merchant or vendor name",
        examples=["Amazon", "Walmart", "Unknown Online Store"]
    )
    reason: str = Field(
        description="Reason for dispute or nature of fraud",
        examples=["Unauthorized charge", "Service not received", "Incorrect amount"]
    )
    is_fraud: bool = Field(
        default=False,
        description="Whether this is reported as fraudulent activity"
    )
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is positive"""
        if v is not None and v < 0:
            raise ValueError("Amount must be positive")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN123456",
                "amount": 49.99,
                "transaction_date": "2024-02-10",
                "merchant": "Amazon",
                "reason": "Item never received",
                "is_fraud": False
            }
        }


class StatementEntity(BaseModel):
    """Extracted statement request information"""
    
    statement_type: str = Field(
        default="monthly",
        description="Type of statement requested",
        examples=["monthly", "annual", "tax", "specific_period"]
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for statement period (YYYY-MM-DD)",
        examples=["2024-01-01"]
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for statement period (YYYY-MM-DD)",
        examples=["2024-01-31"]
    )
    delivery_method: str = Field(
        default="email",
        description="How to deliver the statement",
        examples=["email", "mail", "online_portal"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "statement_type": "monthly",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "delivery_method": "email"
            }
        }


class PaymentEntity(BaseModel):
    """Extracted payment information"""
    
    payment_type: str = Field(
        description="Type of payment issue or action",
        examples=["schedule", "cancel", "failed", "pending"]
    )
    amount: Optional[float] = Field(
        default=None,
        description="Payment amount in dollars"
    )
    payment_date: Optional[str] = Field(
        default=None,
        description="Scheduled or actual payment date (YYYY-MM-DD)"
    )
    payment_method: Optional[str] = Field(
        default=None,
        description="Payment method used or to be used",
        examples=["checking", "savings", "debit_card"]
    )
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount is positive"""
        if v is not None and v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class CardEntity(BaseModel):
    """Extracted card-related information"""
    
    card_last_four: Optional[str] = Field(
        default=None,
        description="Last 4 digits of card number",
        pattern=r"^\d{4}$"
    )
    card_type: Optional[str] = Field(
        default=None,
        description="Type of card",
        examples=["debit", "credit", "prepaid"]
    )
    action: str = Field(
        description="Card action needed",
        examples=["activate", "replace", "report_lost", "report_stolen"]
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for card action",
        examples=["lost", "stolen", "damaged", "expired"]
    )
    
    @validator('card_last_four')
    def validate_card_digits(cls, v):
        """Validate card digits"""
        if v and (not v.isdigit() or len(v) != 4):
            raise ValueError("Card last four must be 4 digits")
        return v


class GenericEntity(BaseModel):
    """Generic entity for intents without specific structure"""
    
    summary: str = Field(
        description="Summary of the customer's request"
    )
    key_details: Optional[List[str]] = Field(
        default=None,
        description="List of key details mentioned in the request"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Customer asking about account balance",
                "key_details": ["checking account", "available balance"]
            }
        }
