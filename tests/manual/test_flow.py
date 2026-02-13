"""
Quick test script to debug the end-to-end flow.
"""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from omni_channel_ai_servicing.graph.registry import get_master_router_graph, get_initial_state
from omni_channel_ai_servicing.integrations import create_clients


async def test_address_update_query():
    """Test a simple address update query"""
    print("\n" + "="*80)
    print("Testing: 'How do I update my mailing address?'")
    print("="*80 + "\n")
    
    try:
        # Create clients
        clients = create_clients()
        print("✓ Created integration clients")
        
        # Get graph
        graph = get_master_router_graph()
        print("✓ Built master router graph")
        
        # Create initial state
        state = get_initial_state(
            user_message="How do I update my mailing address?",
            customer_id="TEST_USER",
            channel="web",
            crm_client=clients.get("crm_client"),
            core_client=clients.get("core_client"),
            notify_client=clients.get("notify_client"),
            workflow_client=clients.get("workflow_client"),
        )
        print("✓ Created initial state")
        print(f"  - User message: {state.user_message}")
        print(f"  - Customer ID: {state.customer_id}")
        print(f"  - Trace ID: {state.trace_id}")
        
        # Execute graph
        print("\n" + "-"*80)
        print("Executing workflow...")
        print("-"*80 + "\n")
        
        result = await graph.ainvoke(state)
        
        print("\n" + "="*80)
        print("RESULTS:")
        print("="*80)
        # LangGraph returns dict, not Pydantic model
        print(f"\nIntent: {result.get('intent')}")
        print(f"Workflow: {result.get('workflow_name')}")
        print(f"Status: {result.get('result', {}).get('status') if result.get('result') else 'N/A'}")
        
        context_metadata = result.get('context_metadata')
        if context_metadata:
            print(f"Retrieved Docs: {context_metadata.get('num_documents', 0)}")
        
        print(f"\nFinal Response:")
        print("-"*80)
        print(result.get('final_response'))
        print("-"*80)
        
        # Show retrieved documents if any
        retrieved_documents = result.get('retrieved_documents')
        if retrieved_documents:
            print(f"\n📚 Retrieved Documents ({len(retrieved_documents)}):")
            for i, doc in enumerate(retrieved_documents[:2], 1):  # Show first 2
                print(f"\n  Document {i}:")
                print(f"  Source: {doc.metadata.get('source', 'unknown')}")
                print(f"  Preview: {doc.page_content[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_query():
    """Test a query that should go to fallback"""
    print("\n" + "="*80)
    print("Testing: 'Hello there'")
    print("="*80 + "\n")
    
    try:
        clients = create_clients()
        graph = get_master_router_graph()
        state = get_initial_state(
            user_message="Hello there",
            customer_id="TEST_USER",
            channel="web",
            **clients
        )
        
        result = await graph.ainvoke(state)
        
        # LangGraph returns dict, not Pydantic model
        print(f"\nIntent: {result.get('intent')}")
        print(f"Workflow: {result.get('workflow_name')}")
        response = result.get('final_response', '')
        print(f"\nResponse: {response[:200] if response else 'N/A'}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RAG WORKFLOW INTEGRATION TEST")
    print("="*80)
    
    # Test 1: Address update (should use RAG)
    success1 = await test_address_update_query()
    
    # Test 2: Fallback (no RAG needed)
    success2 = await test_fallback_query()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Address Update Query: {'✓ PASS' if success1 else '✗ FAIL'}")
    print(f"Fallback Query: {'✓ PASS' if success2 else '✗ FAIL'}")
    print("="*80 + "\n")
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
