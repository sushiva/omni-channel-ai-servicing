"""
LLM Prompts with guardrails for the omni-channel AI servicing platform.
"""

# Import guardrail templates
from src.services.guardrails import SYSTEM_PROMPT_GUARDRAILS, get_guardrail_prompt


INTENT_PROMPT = """
You are an intent classifier for a banking assistant.

{guardrails}

Classify the user's message into one of these intents:

- update_address: Customer wants to change their mailing/billing address
- request_statement: Customer wants to view or download account statements
- dispute_transaction: Customer wants to dispute or challenge a charge they recognize but disagree with (wrong amount, double charge, returned item, etc.)
- report_fraud: Customer wants to report unauthorized or fraudulent activity they did NOT initiate (stolen card, identity theft, etc.)
- unknown: For any other request

Examples:
- "I need to update my address to 123 Main St" → update_address
- "Please change my mailing address" → update_address
- "I moved and need to update my address" → update_address
- "Can I get my account statement for last month?" → request_statement
- "Please send me my statement" → request_statement
- "I want to dispute a charge from MegaMart" → dispute_transaction
- "This charge of $250 is incorrect, I want to dispute it" → dispute_transaction
- "I see a transaction I didn't make, someone stole my card" → report_fraud
- "There are unauthorized charges on my account" → report_fraud
- "Someone used my card without permission" → report_fraud

User message:
"{message}"

Return ONLY the intent name, nothing else.
"""

ENTITY_PROMPT = """
Extract structured entities from the user's message.

{guardrails}

IMPORTANT: NEVER make up or hallucinate information. Only extract what is explicitly stated.

For address updates, extract:
- street
- city
- state
- zip

For transaction disputes, extract:
- transaction_id (e.g., TXN-12345, transaction number)
- amount (numeric value in dollars)
- merchant (merchant/store name)
- dispute_reason (brief reason for dispute)

Return JSON only. Only include fields relevant to the user's request.
If information is missing, leave it out - do NOT make it up.

User message:
"{message}"
"""
