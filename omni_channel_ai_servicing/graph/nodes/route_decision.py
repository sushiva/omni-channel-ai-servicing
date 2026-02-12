async def route_decision_node(state):
    intent = state.intent

    if intent == "update_address":
        return {"next": "update_address"}
    elif intent == "request_statement":
        return {"next": "create_case"}
    else:
        return {"next": "generate_response"}
