"""
Master Router Graph - Entry point for all customer service requests.

This graph orchestrates the routing of customer requests to specialized
workflow sub-graphs based on intent classification.

Flow:
    START
      ↓
    classify_intent (determines what the customer wants)
      ↓
    route_to_workflow (maps intent to workflow name)
      ↓
    [Conditional routing to specialized workflow]
      ↓ 
    address_workflow | fallback_workflow | ...
      ↓
    END
"""
from langgraph.graph import StateGraph
from src.graph.state import AppState
from src.graph.nodes.classify_intent import classify_intent_node
from src.graph.nodes.route_to_workflow import route_to_workflow_node
from src.graph.workflows.address_update_graph import build_address_update_graph
from src.graph.workflows.dispute_graph import build_dispute_graph
from src.graph.workflows.fallback_graph import build_fallback_graph


def build_master_router_graph():
    """
    Builds the master orchestrator graph that routes requests to specialized workflows.
    
    Uses conditional edges to dynamically route based on workflow_name field.
    Each workflow is a compiled sub-graph that processes the request.
    """
    graph = StateGraph(AppState)
    
    # Add routing nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("route_to_workflow", route_to_workflow_node)
    
    # Add workflow sub-graphs as nodes
    graph.add_node("address_workflow", build_address_update_graph())
    graph.add_node("dispute_workflow", build_dispute_graph())
    graph.add_node("fallback_workflow", build_fallback_graph())
    
    # TODO: Add more workflows as they're implemented
    # graph.add_node("statement_workflow", build_statement_workflow())
    # graph.add_node("fraud_workflow", build_fraud_workflow())
    
    # Entry point: classify the customer's intent
    graph.set_entry_point("classify_intent")
    
    # After classification, determine which workflow to use
    graph.add_edge("classify_intent", "route_to_workflow")
    
    # Conditional routing: based on workflow_name, route to appropriate sub-graph
    graph.add_conditional_edges(
        "route_to_workflow",
        lambda state: state.workflow_name,
        {
            "address_workflow": "address_workflow",
            "dispute_workflow": "dispute_workflow",
            "fallback_workflow": "fallback_workflow",
        }
    )
    
    # Each workflow sub-graph will handle its own completion and set final_response
    # No need for explicit finish edges - sub-graphs are terminal
    
    return graph.compile()
