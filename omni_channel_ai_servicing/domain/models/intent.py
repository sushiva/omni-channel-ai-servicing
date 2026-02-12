"""
Domain models for customer intents.
Defines all possible intents the system can handle.
"""
from enum import Enum


class CustomerIntent(str, Enum):
    """
    Enumeration of all possible customer service intents.
    
    Used for type-safe intent classification and routing to appropriate workflows.
    """
    
    ADDRESS_UPDATE = "address_update"
    """Customer wants to update their mailing or billing address"""
    
    FRAUD_REPORT = "fraud_report"
    """Customer is reporting fraudulent activity on their account"""
    
    DISPUTE = "dispute"
    """Customer is disputing a charge or transaction"""
    
    STATEMENT_REQUEST = "statement_request"
    """Customer is requesting account statements"""
    
    ACCOUNT_INQUIRY = "account_inquiry"
    """General questions about account balance, status, or details"""
    
    PAYMENT_ISSUE = "payment_issue"
    """Issues with payments (failed, pending, scheduling)"""
    
    CARD_ACTIVATION = "card_activation"
    """Customer needs to activate a new card"""
    
    CARD_REPLACEMENT = "card_replacement"
    """Customer needs to replace a lost, stolen, or damaged card"""
    
    BALANCE_INQUIRY = "balance_inquiry"
    """Customer wants to check their account balance"""
    
    FALLBACK = "fallback"
    """Catch-all for intents that don't match any specific category"""
    
    @classmethod
    def get_description(cls, intent: 'CustomerIntent') -> str:
        """Get human-readable description of an intent"""
        descriptions = {
            cls.ADDRESS_UPDATE: "Address update request",
            cls.FRAUD_REPORT: "Fraud or suspicious activity report",
            cls.DISPUTE: "Transaction dispute",
            cls.STATEMENT_REQUEST: "Statement or document request",
            cls.ACCOUNT_INQUIRY: "Account information inquiry",
            cls.PAYMENT_ISSUE: "Payment problem or question",
            cls.CARD_ACTIVATION: "New card activation",
            cls.CARD_REPLACEMENT: "Card replacement request",
            cls.BALANCE_INQUIRY: "Balance check",
            cls.FALLBACK: "Unrecognized or ambiguous request"
        }
        return descriptions.get(intent, "Unknown intent")
