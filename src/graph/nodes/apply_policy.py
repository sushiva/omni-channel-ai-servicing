from src.graph.nodes import log_node


@log_node("apply_policy")
async def apply_policy_node(state):
    # Placeholder — real version will check RAG + rules
    if state.intent == "unknown":
        return {"result": {"error": "Unable to determine intent"}}

    # TODO: evaluate customer_risk policy here once the policy engine is wired up.
    #   - Load risk tier from state.risk_tier (default to "medium")
    #   - Apply tier-specific rate limits and channel blocks
    #   - If tier requires human review, set result accordingly

    return {}  # no policy violations
