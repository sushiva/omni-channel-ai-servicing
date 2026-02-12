from langgraph.graph import StateGraph
from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.nodes.classify_intent import classify_intent_node
from omni_channel_ai_servicing.graph.nodes.extract_entities import extract_entities_node
from omni_channel_ai_servicing.graph.nodes.apply_policy import apply_policy_node
from omni_channel_ai_servicing.graph.nodes.route_decision import route_decision_node
from omni_channel_ai_servicing.graph.nodes.update_address import update_address_node
from omni_channel_ai_servicing.graph.nodes.create_case import create_case_node
from omni_channel_ai_servicing.graph.nodes.generate_response import generate_response_node


def _policy_check(state) -> str:
    if state.result and "error" in state.result:
        return "generate_response"
    return "route_decision"


def build_address_update_graph():
    graph = StateGraph(AppState)

    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("extract_entities", extract_entities_node)
    graph.add_node("apply_policy", apply_policy_node)
    graph.add_node("route_decision", route_decision_node)
    graph.add_node("update_address", update_address_node)
    graph.add_node("create_case", create_case_node)
    graph.add_node("generate_response", generate_response_node)

    graph.set_entry_point("classify_intent")

    graph.add_edge("classify_intent", "extract_entities")
    graph.add_edge("extract_entities", "apply_policy")

    # Short-circuit to response on policy violation
    graph.add_conditional_edges(
        "apply_policy",
        _policy_check,
        {
            "route_decision": "route_decision",
            "generate_response": "generate_response",
        }
    )

    graph.add_conditional_edges(
        "route_decision",
        lambda state: state.next,
        {
            "update_address": "update_address",
            "create_case": "create_case",
            "generate_response": "generate_response",
        }
    )

    graph.add_edge("update_address", "generate_response")
    graph.add_edge("create_case", "generate_response")

    return graph.compile()
