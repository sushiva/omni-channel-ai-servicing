import json
from omni_channel_ai_servicing.llm.prompts import ENTITY_PROMPT
from omni_channel_ai_servicing.graph.nodes import log_node


@log_node("extract_entities")
async def extract_entities_node(state):
    prompt = ENTITY_PROMPT.format(message=state.user_message)
    raw = await state.llm.run(prompt)

    try:
        entities = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        entities = {}

    return {"entities": entities}
