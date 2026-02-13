"""
Test RAG context retrieval node in isolation (no LLM required).

Tests Phase 3 retrieve_context node without full workflow execution.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omni_channel_ai_servicing.graph.state import AppState
from omni_channel_ai_servicing.graph.nodes.retrieve_context import retrieve_context_node


async def test_retrieve_address_policy():
    """Test retrieving address update policy."""
    print("\n" + "="*80)
    print("TEST 1: Retrieve Address Update Policy")
    print("="*80)
    
    state = AppState(
        user_message="How do I update my address?",
        intent="ADDRESS_UPDATE",
        customer_id="CUST-001"
    )
    
    print(f"Query: {state.user_message}")
    print(f"Intent: {state.intent}")
    
    result = await retrieve_context_node(state)
    
    print("\n--- Results ---")
    print(f"Documents retrieved: {len(result.get('retrieved_documents', []))}")
    
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        if metadata.get('skipped'):
            print(f"Skipped: {metadata.get('reason')}")
        else:
            print(f"Avg score: {metadata.get('avg_score', 0):.3f}")
            print(f"Top score: {metadata.get('top_score', 0):.3f}")
    
    if result.get('context'):
        print(f"\nContext preview (first 200 chars):")
        print(result['context'][:200] + "...")
    
    return result


async def test_retrieve_dispute_policy():
    """Test retrieving dispute policy."""
    print("\n" + "="*80)
    print("TEST 2: Retrieve Dispute Policy")
    print("="*80)
    
    state = AppState(
        user_message="I was charged twice. How do I dispute this?",
        intent="DISPUTE",
        customer_id="CUST-002"
    )
    
    print(f"Query: {state.user_message}")
    print(f"Intent: {state.intent}")
    
    result = await retrieve_context_node(state)
    
    print("\n--- Results ---")
    print(f"Documents retrieved: {len(result.get('retrieved_documents', []))}")
    
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        if metadata.get('skipped'):
            print(f"Skipped: {metadata.get('reason')}")
        else:
            print(f"Avg score: {metadata.get('avg_score', 0):.3f}")
            print(f"Top score: {metadata.get('top_score', 0):.3f}")
    
    if result.get('context'):
        print(f"\nContext preview (first 200 chars):")
        print(result['context'][:200] + "...")
    
    return result


async def test_skip_retrieval_greeting():
    """Test that greetings skip retrieval."""
    print("\n" + "="*80)
    print("TEST 3: Greeting (Should Skip Retrieval)")
    print("="*80)
    
    state = AppState(
        user_message="Hello!",
        intent="GREETING",
        customer_id="CUST-003"
    )
    
    print(f"Query: {state.user_message}")
    print(f"Intent: {state.intent}")
    
    result = await retrieve_context_node(state)
    
    print("\n--- Results ---")
    
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        if metadata.get('skipped'):
            print(f"✓ Correctly skipped: {metadata.get('reason')}")
        else:
            print(f"✗ Should have skipped but didn't!")
    
    return result


async def test_fraud_reporting():
    """Test retrieving fraud reporting policy."""
    print("\n" + "="*80)
    print("TEST 4: Retrieve Fraud Reporting Policy")
    print("="*80)
    
    state = AppState(
        user_message="How do I report fraudulent charges on my account?",
        intent="FRAUD_REPORT",
        customer_id="CUST-004"
    )
    
    print(f"Query: {state.user_message}")
    print(f"Intent: {state.intent}")
    
    result = await retrieve_context_node(state)
    
    print("\n--- Results ---")
    print(f"Documents retrieved: {len(result.get('retrieved_documents', []))}")
    
    if result.get('context_metadata'):
        metadata = result['context_metadata']
        if metadata.get('skipped'):
            print(f"Skipped: {metadata.get('reason')}")
        else:
            print(f"Avg score: {metadata.get('avg_score', 0):.3f}")
            print(f"Top score: {metadata.get('top_score', 0):.3f}")
    
    if result.get('context'):
        print(f"\nContext preview (first 200 chars):")
        print(result['context'][:200] + "...")
    
    return result


async def main():
    """Run all retrieval tests."""
    print("\n" + "="*80)
    print("Phase 3: RAG Context Retrieval Tests (No LLM Required)")
    print("="*80)
    
    try:
        # Test retrieval for different policies
        result1 = await test_retrieve_address_policy()
        result2 = await test_retrieve_dispute_policy()
        result3 = await test_skip_retrieval_greeting()
        result4 = await test_fraud_reporting()
        
        # Summary
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)
        
        tests_passed = 0
        total_tests = 4
        
        # Check test 1 - should retrieve context
        if (result1.get('retrieved_documents') and 
            len(result1['retrieved_documents']) > 0 and
            not result1.get('context_metadata', {}).get('skipped')):
            print("✓ Test 1: Retrieved address update policy")
            tests_passed += 1
        else:
            print("✗ Test 1: Failed to retrieve address update policy")
        
        # Check test 2 - should retrieve context
        if (result2.get('retrieved_documents') and 
            len(result2['retrieved_documents']) > 0 and
            not result2.get('context_metadata', {}).get('skipped')):
            print("✓ Test 2: Retrieved dispute policy")
            tests_passed += 1
        else:
            print("✗ Test 2: Failed to retrieve dispute policy")
        
        # Check test 3 - should skip
        if result3.get('context_metadata', {}).get('skipped'):
            print("✓ Test 3: Correctly skipped retrieval for greeting")
            tests_passed += 1
        else:
            print("✗ Test 3: Should have skipped retrieval")
        
        # Check test 4 - should retrieve context
        if (result4.get('retrieved_documents') and 
            len(result4['retrieved_documents']) > 0 and
            not result4.get('context_metadata', {}).get('skipped')):
            print("✓ Test 4: Retrieved fraud reporting policy")
            tests_passed += 1
        else:
            print("✗ Test 4: Failed to retrieve fraud reporting policy")
        
        print(f"\nPassed: {tests_passed}/{total_tests}")
        
        # Print retrieval metrics
        print("\n--- Retrieval Metrics ---")
        
        retrieval_results = [
            ("Address Update", result1),
            ("Dispute", result2),
            ("Fraud Report", result4)
        ]
        
        for name, result in retrieval_results:
            if result.get('context_metadata') and not result['context_metadata'].get('skipped'):
                meta = result['context_metadata']
                print(f"{name}:")
                print(f"  - Documents: {meta.get('num_documents', 0)}")
                print(f"  - Avg score: {meta.get('avg_score', 0):.3f}")
                print(f"  - Top score: {meta.get('top_score', 0):.3f}")
        
        if tests_passed == total_tests:
            print("\n🎉 All retrieval tests passed!")
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
