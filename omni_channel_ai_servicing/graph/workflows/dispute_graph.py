"""
Dispute Resolution Workflow Graph.

Handles transaction dispute requests with the following flow:
1. Classify intent (already done by master router)
2. Extract dispute details (transaction ID, amount, merchant, reason)
3. Apply policy checks (dispute eligibility, time limits)
4. Route decision (create case vs reject)
5. Create dispute case
6. Generate response

Similar to address_update_graph but specialized for disputes.
"""
from langgraph.graph import StateGraph
from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.nodes.classify_intent import classify_intent_node
from omni_channel_ai_servicing.graph.nodes.extract_entities import extract_entities_node
from omni_channel_ai_servicing.graph.nodes.apply_policy import apply_policy_node
from omni_channel_ai_servicing.graph.nodes.create_dispute_case import create_dispute_case_node
from omni_channel_ai_servicing.graph.nodes.generate_response import generate_response_node


def _dispute_policy_check(state) -> str:
    """
    Check if dispute passes policy validation.
    If there's an error, skip to response generation.
    """
    if state.result and "error" in state.result:
        return "generate_response"
    return "create_dispute_case"


def build_dispute_graph():
    """
    Build the dispute resolution workflow graph.
    
    Flow:
        classify_intent → extract_entities → apply_policy
                                                ↓
                            [policy check] → create_dispute_case → generate_response
                                  ↓
                            [policy fail] → generate_response
    """
    graph = StateGraph(AppState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("apply_policy", apply_policy_node)
    graph.add_node("create_dispute_case", create_dispute_case_node)
    graph.add_node("generate_response", generate_response_node)

    # Set entry point
    graph.set_entry_point("classify_intent")

    # Linear flow through classification and extraction
    graph.add_edge("classify_intent", "extract_entities")
    graph.add_edge("extract_entities", "apply_policy")

    # Conditional routing after policy check
    graph.add_conditional_edges(
        "apply_policy",
        _dispute_policy_check,
        {
            "create_dispute_case": "create_dispute_case",
            "generate_response": "generate_response",
        }
    )

    # Create case then generate response
    graph.add_edge("create_dispute_case", "generate_response")

    return graph.compile()
