from omni_channel_ai_servicing.llm.prompts import INTENT_PROMPT
from omni_channel_ai_servicing.graph.nodes import log_node
from omni_channel_ai_servicing.monitoring.logger import get_logger
from omni_channel_ai_servicing.llm.output_parsers import intent_parser, get_intent_format_instructions
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from langchain_core.exceptions import OutputParserException

logger = get_logger("classify_intent")


@log_node("classify_intent")
async def classify_intent_node(state):
    # Add format instructions to prompt
    format_instructions = get_intent_format_instructions()
    prompt = INTENT_PROMPT.format(message=state.user_message, guardrails="") + f"\n\n{format_instructions}"
    
    raw = await state.llm.run(prompt)
    
    # Try to parse with structured parser
    try:
        intent_enum: CustomerIntent = intent_parser.parse(raw)
        intent = intent_enum.value
        logger.info(f"Successfully parsed intent: {intent_enum.name} ({intent})")
    except (OutputParserException, ValueError) as e:
        logger.warning(f"Failed to parse intent from '{raw}': {e}. Defaulting to FALLBACK")
        intent = CustomerIntent.FALLBACK.value
    
    logger.info(f"Message: {state.user_message[:100]} -> Intent: {intent}")
    
    return {"intent": intent}
