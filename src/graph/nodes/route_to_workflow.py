from src.graph.nodes import log_node


# Workflows that are currently implemented
IMPLEMENTED_WORKFLOWS = {
    "address_workflow",
    "dispute_workflow",
    "fallback_workflow",
}


@log_node("route_to_workflow")
async def route_to_workflow_node(state):
    """
    Maps intent to workflow name for conditional routing.
    
    Intent -> Workflow Mapping:
    - update_address -> address_workflow
    - request_statement -> statement_workflow (routes to fallback until implemented)
    - report_fraud -> fraud_workflow (routes to fallback until implemented)
    - unknown -> fallback_workflow
    
    If a workflow is not yet implemented, routes to fallback_workflow.
    """
    intent = state.intent
    
    # Map intent to workflow identifier
    workflow_map = {
        "update_address": "address_workflow",
        "dispute_transaction": "dispute_workflow",
        "request_statement": "statement_workflow",
        "report_fraud": "fraud_workflow",
        "unknown": "fallback_workflow",
    }
    
    workflow_name = workflow_map.get(intent, "fallback_workflow")
    
    # If workflow not implemented yet, use fallback
    if workflow_name not in IMPLEMENTED_WORKFLOWS:
        workflow_name = "fallback_workflow"
    
    return {"workflow_name": workflow_name}
