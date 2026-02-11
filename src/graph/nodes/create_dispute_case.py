"""
Node for creating dispute cases in the workflow system.

Handles transaction dispute creation with validation and case management.
"""
from src.graph.nodes import log_node


@log_node("create_dispute_case")
async def create_dispute_case_node(state):
    """
    Create a dispute case for the transaction.
    
    This node:
    1. Validates dispute information (transaction ID, amount, reason)
    2. Creates a case in the workflow management system
    3. Assigns initial priority based on amount and type
    4. Returns case ID for tracking
    """
    entities = state.entities or {}
    customer_id = state.customer_id
    workflow_client = state.workflow_client
    
    # Extract dispute details from entities
    transaction_id = entities.get("transaction_id")
    amount = entities.get("amount")
    dispute_reason = entities.get("dispute_reason", "unspecified")
    merchant = entities.get("merchant")
    
    # Determine priority based on amount
    if amount and float(amount) > 1000:
        priority = "high"
    elif amount and float(amount) > 100:
        priority = "medium"
    else:
        priority = "low"
    
    # Create dispute case
    if not workflow_client:
        return {
            "result": {"error": "Workflow client not configured"},
            "case_id": None
        }
    
    try:
        # Build description
        description = f"Transaction dispute for {merchant or 'merchant'}"
        if transaction_id:
            description += f" (Transaction: {transaction_id})"
        if amount:
            description += f" - Amount: ${amount}"
        description += f" - Reason: {dispute_reason}"
        
        # Create case with proper named parameters
        response = await workflow_client.create_case(
            case_type="dispute",
            description=description,
            priority=priority,
            metadata={
                "customer_id": customer_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "reason": dispute_reason,
                "merchant": merchant
            }
        )
        case_id = response.get("case_id")
        
        return {
            "case_id": case_id,
            "result": {
                "status": "dispute_created",
                "case_id": case_id,
                "priority": priority,
                "transaction_id": transaction_id,
                "amount": amount
            }
        }
    except Exception as e:
        return {
            "result": {"error": f"Failed to create dispute case: {str(e)}"},
            "case_id": None
        }
