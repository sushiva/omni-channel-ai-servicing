from omni_channel_ai_servicing.graph.nodes import log_node


@log_node("update_address")
async def update_address_node(state):
    if not state.core_client:
        return {"result": {"error": "Core banking client not configured"}}

    address = state.entities or {}
    result = await state.core_client.update_address(
        customer_id=state.customer_id,
        address=address,
    )
    return {"result": result}
