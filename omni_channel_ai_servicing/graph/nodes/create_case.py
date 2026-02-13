async def create_case_node(state):
    if not state.crm_client:
        return {"result": {"error": "CRM client not configured"}}

    try:
        result = await state.crm_client.create_case(
            customer_id=state.customer_id,
            intent=state.intent,
            details=state.entities or {}
        )
        
        # Validate response has required 'id' field
        if not result or "id" not in result:
            return {
                "result": {"error": "Invalid CRM response: missing case ID"},
                "case_id": None
            }
        
        return {"case_id": result["id"]}
    except Exception as e:
        return {
            "result": {"error": f"Failed to create case: {str(e)}"},
            "case_id": None
        }
