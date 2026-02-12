from omni_channel_ai_servicing.graph.nodes import log_node


@log_node("generate_response")
async def generate_response_node(state):
    if state.result and "error" in state.result:
        return {"final_response": f"Error: {state.result['error']}"}

    if state.result:
        return {"final_response": f"Done: {state.result}"}

    return {"final_response": "Your request has been processed."}
