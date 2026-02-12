"""
Fallback workflow for unknown or unsupported intents.

Handles cases where intent classification fails or the intent
is not yet supported by a specialized workflow.
"""
from langgraph.graph import StateGraph
from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.nodes.generate_response import generate_response_node


async def fallback_handler_node(state):
    """
    Provides a helpful fallback response when intent is unknown.
    In production, this might:
    - Route to human agent
    - Suggest common intents
    - Log for future training
    """
    fallback_message = (
        "I understand you need assistance, but I'm not quite sure what you're asking for. "
        "I can help you with:\n"
        "- Updating your address\n"
        "- Requesting account statements\n"
        "- Reporting fraud or suspicious activity\n\n"
        "Could you please rephrase your request, or would you like to speak with a representative?"
    )
    
    return {
        "final_response": fallback_message,
        "result": {"status": "fallback", "intent": state.intent}
    }


def build_fallback_graph():
    """
    Simple fallback workflow: just generate a helpful message.
    """
    graph = StateGraph(AppState)
    
    graph.add_node("fallback_handler", fallback_handler_node)
    
    graph.set_entry_point("fallback_handler")
    graph.set_finish_point("fallback_handler")
    
    return graph.compile()
