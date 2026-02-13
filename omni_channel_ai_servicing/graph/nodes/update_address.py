from omni_channel_ai_servicing.graph.nodes import log_node


@log_node("update_address")
async def update_address_node(state):
    if not state.core_client:
        return {"result": {"error": "Core banking client not configured"}}

    try:
        address = state.entities or {}
        result = await state.core_client.update_address(
            customer_id=state.customer_id,
            address=address,
        )
        
        # Validate result is not None
        if result is None:
            return {"result": {"error": "Core banking returned null response", "status": "failed"}}
        
        return {"result": result}
    except Exception as e:
        return {"result": {"error": f"Failed to update address: {str(e)}", "status": "failed"}}
