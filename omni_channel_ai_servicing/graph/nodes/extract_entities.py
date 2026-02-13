import json
from omni_channel_ai_servicing.llm.prompts import ENTITY_PROMPT
from omni_channel_ai_servicing.graph.nodes import log_node
from omni_channel_ai_servicing.monitoring.logger import get_logger
from omni_channel_ai_servicing.llm.output_parsers import get_entity_parser, get_entity_format_instructions
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from langchain_core.exceptions import OutputParserException

logger = get_logger("extract_entities")


@log_node("extract_entities")
async def extract_entities_node(state):
    # Get intent and determine if we need structured parsing
    intent_str = state.intent or "fallback"
    
    try:
        intent = CustomerIntent(intent_str)
    except ValueError:
        logger.warning(f"Unknown intent '{intent_str}', using fallback")
        intent = CustomerIntent.FALLBACK
    
    # Get parser for this intent
    parser = get_entity_parser(intent)
    
    if parser:
        # Use structured parsing
        format_instructions = get_entity_format_instructions(intent)
        prompt = ENTITY_PROMPT.format(message=state.user_message, guardrails="") + f"\n\n{format_instructions}"
        raw = await state.llm.run(prompt)
        
        try:
            entities_obj = parser.parse(raw)
            entities = entities_obj.model_dump()
            logger.info(f"Successfully parsed entities for {intent.name}: {list(entities.keys())}")
        except (OutputParserException, ValueError) as e:
            logger.warning(f"Failed to parse entities: {e}. Falling back to JSON parsing")
            # Fallback to old JSON parsing
            try:
                entities = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                entities = {}
    else:
        # No structured parser, use old approach
        logger.debug(f"No structured parser for {intent.name}, using JSON parsing")
        prompt = ENTITY_PROMPT.format(message=state.user_message, guardrails="")
        raw = await state.llm.run(prompt)
        
        try:
            entities = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse entities as JSON")
            entities = {}

    return {"entities": entities}
