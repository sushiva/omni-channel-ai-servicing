"""
Test RAG-enabled workflow with context retrieval.

Tests the integration of Phase 2 retrieval infrastructure into LangGraph workflows.
"""
import asyncio
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.workflows.address_update_graph import build_address_update_graph
from omni_channel_ai_servicing.graph.workflows.dispute_graph import build_dispute_graph
from langchain_openai import ChatOpenAI


async def test_address_update_with_rag():
    """Test address update workflow with RAG context retrieval."""
    print("\n" + "="*80)
    print("TEST 1: Address Update with RAG")
    print("="*80)
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create initial state
    initial_state = AppState(
        user_message="How do I update my address?",
        channel="chat",
        customer_id="CUST-001",
        llm=llm
    )
    
    # Build and run graph
    graph = build_address_update_graph()
    
    print(f"\nUser message: {initial_state.user_message}")
    print("Running workflow...")
    
    result = await graph.ainvoke(initial_state)
    
    print("\n--- Results ---")
    print(f"Intent: {result.get('intent')}")
    print(f"Entities: {result.get('entities')}")
    
    # Check if context was retrieved
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        print(f"\nContext retrieval:")
        print(f"  - Retrieved: {metadata.get('num_documents', 0)} documents")
        if not metadata.get('skipped'):
            print(f"  - Avg score: {metadata.get('avg_score', 0):.3f}")
            print(f"  - Top score: {metadata.get('top_score', 0):.3f}")
        else:
            print(f"  - Skipped: {metadata.get('reason')}")
    
    print(f"\nFinal response:")
    print(result.get('final_response', 'No response'))
    
    return result


async def test_dispute_with_rag():
    """Test dispute workflow with RAG context retrieval."""
    print("\n" + "="*80)
    print("TEST 2: Dispute with RAG")
    print("="*80)
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create initial state
    initial_state = AppState(
        user_message="I was charged twice for the same transaction. How do I dispute this?",
        channel="chat",
        customer_id="CUST-002",
        llm=llm
    )
    
    # Build and run graph
    graph = build_dispute_graph()
    
    print(f"\nUser message: {initial_state.user_message}")
    print("Running workflow...")
    
    result = await graph.ainvoke(initial_state)
    
    print("\n--- Results ---")
    print(f"Intent: {result.get('intent')}")
    print(f"Entities: {result.get('entities')}")
    
    # Check if context was retrieved
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        print(f"\nContext retrieval:")
        print(f"  - Retrieved: {metadata.get('num_documents', 0)} documents")
        if not metadata.get('skipped'):
            print(f"  - Avg score: {metadata.get('avg_score', 0):.3f}")
            print(f"  - Top score: {metadata.get('top_score', 0):.3f}")
        else:
            print(f"  - Skipped: {metadata.get('reason')}")
    
    print(f"\nFinal response:")
    print(result.get('final_response', 'No response'))
    
    return result


async def test_greeting_without_rag():
    """Test that greetings skip RAG retrieval."""
    print("\n" + "="*80)
    print("TEST 3: Greeting (should skip RAG)")
    print("="*80)
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create initial state
    initial_state = AppState(
        user_message="Hello, how are you?",
        intent="GREETING",  # Pre-set to test skip logic
        channel="chat",
        customer_id="CUST-003",
        llm=llm
    )
    
    # Use address update graph for simplicity
    graph = build_address_update_graph()
    
    print(f"\nUser message: {initial_state.user_message}")
    print(f"Intent: {initial_state.intent}")
    print("Running workflow...")
    
    result = await graph.ainvoke(initial_state)
    
    print("\n--- Results ---")
    
    # Check if context was skipped
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        print(f"\nContext retrieval:")
        if metadata.get('skipped'):
            print(f"  - ✓ Correctly skipped: {metadata.get('reason')}")
        else:
            print(f"  - ✗ Should have skipped but didn't!")
    
    return result


async def main():
    """Run all RAG workflow tests."""
    print("\n" + "="*80)
    print("Phase 3: LangGraph RAG Integration Tests")
    print("="*80)
    
    try:
        # Test 1: Address update with context retrieval
        result1 = await test_address_update_with_rag()
        
        # Test 2: Dispute with context retrieval
        result2 = await test_dispute_with_rag()
        
        # Test 3: Greeting without retrieval
        result3 = await test_greeting_without_rag()
        
        # Summary
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)
        
        tests_passed = 0
        total_tests = 3
        
        # Check test 1
        if result1.get('context_metadata') and not result1['context_metadata'].get('skipped'):
            print("✓ Test 1: Address update retrieved context")
            tests_passed += 1
        else:
            print("✗ Test 1: Address update failed to retrieve context")
        
        # Check test 2
        if result2.get('context_metadata') and not result2['context_metadata'].get('skipped'):
            print("✓ Test 2: Dispute retrieved context")
            tests_passed += 1
        else:
            print("✗ Test 2: Dispute failed to retrieve context")
        
        # Check test 3
        if result3.get('context_metadata') and result3['context_metadata'].get('skipped'):
            print("✓ Test 3: Greeting correctly skipped retrieval")
            tests_passed += 1
        else:
            print("✗ Test 3: Greeting should have skipped retrieval")
        
        print(f"\nPassed: {tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("\n🎉 All RAG integration tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
