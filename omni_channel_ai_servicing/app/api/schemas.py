"""
API Request/Response Schemas for Omni-Channel AI Servicing.

These schemas define the contract between external clients (mobile, web, chat)
and the AI servicing backend.
"""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class ServiceRequest(BaseModel):
    """
    Universal customer service request schema.
    
    Accepts requests from any channel (email, chat, voice, mobile).
    """
    customer_id: str = Field(
        ...,
        description="Unique identifier for the customer",
        examples=["cust123", "user456"],
        min_length=1
    )
    
    message: str = Field(
        ...,
        description="The customer's request or question",
        examples=[
            "I want to update my address to 123 Main St",
            "I need to dispute a charge",
            "How do I report fraud?"
        ],
        min_length=1
    )
    
    @field_validator('customer_id', 'message')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure strings are not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
    channel: Literal["email", "chat", "voice", "mobile", "web"] = Field(
        default="web",
        description="The channel through which the request was received"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (session_id, device_info, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust123",
                "message": "I need to change my address to 456 Oak Ave, Raleigh NC 27601",
                "channel": "email",
                "metadata": {
                    "session_id": "sess_abc123",
                    "locale": "en_US"
                }
            }
        }


class ServiceResponse(BaseModel):
    """
    Standardized response for all service requests.
    """
    request_id: str = Field(
        ...,
        description="Unique trace ID for this request (for debugging/auditing)"
    )
    
    intent: str = Field(
        ...,
        description="Classified intent (update_address, dispute, fraud, etc.)"
    )
    
    workflow: str = Field(
        ...,
        description="Which workflow handled this request"
    )
    
    status: str = Field(
        ...,
        description="Outcome status (success, failure, pending, fallback)"
    )
    
    response: str = Field(
        ...,
        description="Natural language response to the customer"
    )
    
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured result data (for programmatic access)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "a7b13fb8",
                "intent": "update_address",
                "workflow": "address_workflow",
                "status": "success",
                "response": "Your address has been successfully updated to 456 Oak Ave, Raleigh NC 27601.",
                "result": {
                    "address_updated": True,
                    "notification_sent": True
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    services: Dict[str, str] = Field(
        default_factory=lambda: {
            "llm": "operational",
            "database": "operational",
            "integrations": "operational"
        }
    )


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    request_id: Optional[str] = Field(None, description="Request trace ID if available")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
