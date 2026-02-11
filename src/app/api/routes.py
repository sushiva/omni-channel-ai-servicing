"""
API Routes for Omni-Channel AI Servicing.

Exposes REST endpoints for customer service requests through the master router.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from src.app.api.schemas import (
    ServiceRequest,
    ServiceResponse,
    HealthCheckResponse,
    ErrorResponse
)
from src.graph.registry import get_master_router_graph, get_initial_state
from src.integrations import create_clients
from src.monitoring.logger import get_logger

logger = get_logger("api.routes")
router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the service is operational.
    """
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        services={
            "llm": "operational",
            "router": "operational",
            "workflows": "operational"
        }
    )


@router.post(
    "/api/v1/service-request",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Customer Service"],
    summary="Process customer service request",
    description="""
    Universal endpoint for processing customer service requests from any channel.
    
    The request is automatically:
    1. Classified by intent (address update, dispute, fraud, etc.)
    2. Routed to the appropriate specialized workflow
    3. Processed with business rules and policies applied
    4. Returns a natural language response to the customer
    
    Supports channels: email, chat, voice, mobile, web
    """
)
async def handle_service_request(request: ServiceRequest) -> ServiceResponse:
    """
    Main entry point for all customer service requests.
    
    This endpoint orchestrates the entire request lifecycle:
    - Intent classification
    - Workflow routing
    - Business logic execution
    - Response generation
    """
    try:
        logger.info(
            "Received service request",
            extra={
                "extra": {
                    "customer_id": request.customer_id,
                    "channel": request.channel,
                    "message_preview": request.message[:50]
                }
            }
        )
        
        # Create integration clients
        clients = create_clients()
        
        # Get master router graph
        graph = get_master_router_graph()
        
        # Create initial state
        state = get_initial_state(
            user_message=request.message,
            customer_id=request.customer_id,
            channel=request.channel,
            crm_client=clients.get("crm_client"),
            core_client=clients.get("core_client"),
            notify_client=clients.get("notify_client"),
            workflow_client=clients.get("workflow_client"),
        )
        
        # Execute the master router (will automatically classify and route)
        result = await graph.ainvoke(state)
        
        # Extract results
        intent = result.get("intent", "unknown")
        workflow_name = result.get("workflow_name", "unknown")
        final_response = result.get("final_response", "Unable to process request")
        workflow_result = result.get("result", {})
        trace_id = result.get("trace_id", "unknown")
        
        # Determine status
        result_status = workflow_result.get("status", "unknown")
        if result_status == "fallback":
            api_status = "fallback"
        elif "error" in workflow_result:
            api_status = "error"
        elif result_status in ["address updated", "case created"]:
            api_status = "success"
        else:
            api_status = result_status
        
        logger.info(
            "Service request completed",
            extra={
                "extra": {
                    "request_id": trace_id,
                    "customer_id": request.customer_id,
                    "intent": intent,
                    "workflow": workflow_name,
                    "status": api_status
                }
            }
        )
        
        return ServiceResponse(
            request_id=trace_id,
            intent=intent,
            workflow=workflow_name,
            status=api_status,
            response=final_response,
            result=workflow_result
        )
        
    except Exception as e:
        logger.error(
            "Error processing service request",
            extra={
                "extra": {
                    "customer_id": request.customer_id,
                    "error": str(e)
                }
            },
            exc_info=True
        )
        
        # Return structured error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An error occurred while processing your request. Please try again later.",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get("/api/v1/intents", tags=["System"])
async def list_supported_intents() -> Dict[str, Any]:
    """
    List all supported intents and their corresponding workflows.
    
    Useful for documentation and client integration.
    """
    return {
        "intents": [
            {
                "intent": "update_address",
                "workflow": "address_workflow",
                "status": "implemented",
                "description": "Update customer mailing or billing address"
            },
            {
                "intent": "dispute_transaction",
                "workflow": "dispute_workflow",
                "status": "implemented",
                "description": "Dispute a transaction or charge"
            },
            {
                "intent": "request_statement",
                "workflow": "statement_workflow",
                "status": "pending",
                "description": "Request account statements"
            },
            {
                "intent": "report_fraud",
                "workflow": "fraud_workflow",
                "status": "pending",
                "description": "Report fraudulent activity"
            },
            {
                "intent": "unknown",
                "workflow": "fallback_workflow",
                "status": "implemented",
                "description": "Fallback for unrecognized requests"
            }
        ],
        "channels": ["email", "chat", "voice", "mobile", "web"]
    }
