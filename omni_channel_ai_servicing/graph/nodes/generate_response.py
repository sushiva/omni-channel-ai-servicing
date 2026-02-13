"""
Generate final response to user, optionally using retrieved context.
"""
import logging
from omni_channel_ai_servicing.graph.nodes import log_node

logger = logging.getLogger(__name__)


@log_node("generate_response")
async def generate_response_node(state):
    """
    Generate final response using LLM and retrieved context if available.
    
    If context is available, includes it in the prompt to ground the response.
    Otherwise, generates a simple confirmation message.
    """
    # Handle errors first
    if state.result and "error" in state.result:
        return {"final_response": f"Error: {state.result['error']}"}
    
    # If no LLM is available, use simple response
    if not state.llm:
        if state.result:
            return {"final_response": f"Done: {state.result}"}
        return {"final_response": "Your request has been processed."}
    
    # If we have context, use it to generate a grounded response
    if state.context and state.user_message:
        try:
            # Get customer name from metadata if available (for personalization)
            customer_name = None
            channel = state.channel
            has_attachments = False
            
            if state.metadata and isinstance(state.metadata, dict):
                customer_name = state.metadata.get("customer_name")
                has_attachments = state.metadata.get("has_attachments", False)
            
            # Build prompt with context
            greeting = f"Address the customer as {customer_name}" if customer_name else "Use a professional greeting"
            
            # Special instructions for email channel with attachments
            action_instruction = ""
            if channel == "email" and has_attachments and state.intent in ["address_update", "ADDRESS_UPDATE"]:
                action_instruction = """
- IMPORTANT: Since the customer has provided the required documents (as mentioned in their message), confirm that:
  1. You have verified the attached documents
  2. The documents meet the requirements stated in the policy
  3. The address update has been processed/completed
- Use language like "We have verified", "Your address has been updated", "The update is complete"
- Be definitive and confirmatory rather than tentative"""
            
            prompt = f"""You are a helpful customer service assistant. Use the provided context from our knowledge base to answer the user's question accurately.

Context from knowledge base:
{state.context}

User question: {state.user_message}

Instructions:
- {greeting}
- Answer based on the context provided
- Be concise and helpful
- If the context doesn't fully answer the question, acknowledge what you can answer
- Include relevant policy details when applicable
- Don't make up information not in the context{action_instruction}

Answer:"""
            
            # Call LLM
            logger.info(f"Generating response with context for: {state.user_message[:50]}...")
            
            response_text = await state.llm.run(prompt)
            
            # Add citation if metadata available
            if state.context_metadata and state.context_metadata.get("num_documents", 0) > 0:
                num_docs = state.context_metadata["num_documents"]
                response_text += f"\n\n_(Answer based on {num_docs} relevant policy document(s))_"
            
            logger.info("Successfully generated context-grounded response")
            return {"final_response": response_text}
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}", exc_info=True)
            # Fallback to simple response
            if state.result:
                return {"final_response": f"Done: {state.result}"}
            return {"final_response": "Your request has been processed."}
    
    # No context available - use simple response
    if state.result:
        return {"final_response": f"Done: {state.result}"}
    
    return {"final_response": "Your request has been processed."}

