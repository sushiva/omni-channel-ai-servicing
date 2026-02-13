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
            # Build prompt with context
            prompt = f"""You are a helpful customer service assistant. Use the provided context from our knowledge base to answer the user's question accurately.

Context from knowledge base:
{state.context}

User question: {state.user_message}

Instructions:
- Answer based on the context provided
- Be concise and helpful
- If the context doesn't fully answer the question, acknowledge what you can answer
- Include relevant policy details when applicable
- Don't make up information not in the context

Answer:"""
            
            # Call LLM
            logger.info(f"Generating response with context for: {state.user_message[:50]}...")
            
            # Handle both sync and async LLM interfaces
            if hasattr(state.llm, 'ainvoke'):
                response = await state.llm.ainvoke(prompt)
            else:
                response = state.llm.invoke(prompt)
            
            # Extract text from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
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

