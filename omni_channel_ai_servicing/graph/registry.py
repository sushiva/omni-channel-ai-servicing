from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.workflows.address_update_graph import build_address_update_graph
from omni_channel_ai_servicing.graph.workflows.dispute_graph import build_dispute_graph
from omni_channel_ai_servicing.graph.workflows.fallback_graph import build_fallback_graph
from omni_channel_ai_servicing.graph.workflows.master_router_graph import build_master_router_graph
from omni_channel_ai_servicing.llm.client import LLMClient

llm = LLMClient()


# Workflow Registry: Maps workflow names to their builder functions
WORKFLOW_REGISTRY = {
    "address_workflow": build_address_update_graph,
    "dispute_workflow": build_dispute_graph,
    "fallback_workflow": build_fallback_graph,
    # Add more workflows as they're implemented:
    # "statement_workflow": build_statement_workflow,
    # "fraud_workflow": build_fraud_workflow,
}


def get_workflow_graph(workflow_name: str):
    """
    Get a compiled graph for a specific workflow.
    
    Args:
        workflow_name: Name of the workflow (e.g., "address_workflow")
        
    Returns:
        Compiled LangGraph workflow
        
    Raises:
        ValueError: If workflow_name is not registered
    """
    builder = WORKFLOW_REGISTRY.get(workflow_name)
    if not builder:
        raise ValueError(
            f"Unknown workflow: {workflow_name}. "
            f"Available workflows: {list(WORKFLOW_REGISTRY.keys())}"
        )
    return builder()


def get_master_router_graph():
    """
    Get the master router graph that orchestrates all workflows.
    
    This is the main entry point for all customer service requests.
    """
    return build_master_router_graph()


def get_graph():
    """
    DEPRECATED: Use get_master_router_graph() for new code.
    
    Returns the master router graph for backward compatibility.
    """
    return get_master_router_graph()


def get_initial_state(user_message: str, customer_id: str, **kwargs):
    """
    Create initial state for a customer service request.
    
    Args:
        user_message: The customer's request text
        customer_id: Unique customer identifier
        **kwargs: Optional arguments (channel, clients, etc.)
    """
    return AppState(
        user_message=user_message,
        customer_id=customer_id,
        channel=kwargs.get("channel", "unknown"),
        crm_client=kwargs.get("crm_client"),
        core_client=kwargs.get("core_client"),
        notify_client=kwargs.get("notify_client"),
        workflow_client=kwargs.get("workflow_client"),
        llm=llm,
    )

