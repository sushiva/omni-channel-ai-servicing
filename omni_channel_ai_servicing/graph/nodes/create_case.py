async def create_case_node(state):
    if not state.crm_client:
        return {"result": {"error": "CRM client not configured"}}

    result = await state.crm_client.create_case(
        customer_id=state.customer_id,
        intent=state.intent,
        details=state.entities or {}
    )
    return {"case_id": result["id"]}
