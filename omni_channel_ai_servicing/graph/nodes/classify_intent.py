from omni_channel_ai_servicing.llm.prompts import INTENT_PROMPT
from omni_channel_ai_servicing.graph.nodes import log_node
from omni_channel_ai_servicing.monitoring.logger import get_logger

logger = get_logger("classify_intent")

VALID_INTENTS = {"update_address", "request_statement", "report_fraud", "dispute_transaction", "unknown"}


@log_node("classify_intent")
async def classify_intent_node(state):
    prompt = INTENT_PROMPT.format(message=state.user_message)
    raw = await state.llm.run(prompt)
    intent = raw.strip().lower()
    
    # Debug: Log what LLM actually returned
    logger.info(f"LLM raw response: '{raw}' -> cleaned: '{intent}'")
    logger.info(f"Message was: {state.user_message[:100]}")

    if intent not in VALID_INTENTS:
        logger.warning(f"Intent '{intent}' not in VALID_INTENTS, defaulting to unknown")
        intent = "unknown"

    return {"intent": intent}
