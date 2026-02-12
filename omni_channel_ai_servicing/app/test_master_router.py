"""
Test script for the master router graph.

This script validates that customer requests are properly routed
through the master router to the correct specialized workflow.
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from omni_channel_ai_servicing.app.config.settings import MOCK_SERVICES_BASE_URL
from omni_channel_ai_servicing.graph.registry import get_master_router_graph, get_initial_state
from omni_channel_ai_servicing.integrations.core_banking_client import CoreBankingClient
from omni_channel_ai_servicing.integrations.crm_client import CRMClient
from omni_channel_ai_servicing.integrations.notification_client import NotificationClient
from omni_channel_ai_servicing.monitoring.logger import get_logger

logger = get_logger("test_master_router")


async def test_address_update_routing():
    """Test that address update requests route to address_workflow"""
    logger.info("=" * 60)
    logger.info("TEST 1: Address Update Routing")
    logger.info("=" * 60)
    
    core_client = CoreBankingClient(base_url=MOCK_SERVICES_BASE_URL)
    crm_client = CRMClient(base_url=MOCK_SERVICES_BASE_URL)
    notify_client = NotificationClient(base_url=MOCK_SERVICES_BASE_URL)

    # Get master router graph (not address_update_graph directly)
    graph = get_master_router_graph()
    
    # Create state with address update request
    state = get_initial_state(
        user_message="I want to change my address to 456 Oak Ave, Raleigh NC 27601",
        customer_id="cust123",
        channel="email",
        core_client=core_client,
        crm_client=crm_client,
        notify_client=notify_client,
    )

    result = await graph.ainvoke(state)

    logger.info("Test 1 Results:")
    logger.info(f"  Intent: {result.get('intent')}")
    logger.info(f"  Workflow: {result.get('workflow_name')}")
    logger.info(f"  Status: {result.get('result', {}).get('status')}")
    logger.info(f"  Response: {result.get('final_response')[:100]}...")
    
    assert result.get('intent') == 'update_address', "Intent should be update_address"
    assert result.get('workflow_name') == 'address_workflow', "Should route to address_workflow"
    
    print("✅ Test 1 PASSED: Address update routed correctly\n")


async def test_unknown_intent_routing():
    """Test that unknown intents route to fallback_workflow"""
    logger.info("=" * 60)
    logger.info("TEST 2: Unknown Intent Fallback Routing")
    logger.info("=" * 60)
    
    core_client = CoreBankingClient(base_url=MOCK_SERVICES_BASE_URL)
    crm_client = CRMClient(base_url=MOCK_SERVICES_BASE_URL)
    notify_client = NotificationClient(base_url=MOCK_SERVICES_BASE_URL)

    graph = get_master_router_graph()
    
    # Create state with unclear request
    state = get_initial_state(
        user_message="What is the meaning of life?",
        customer_id="cust456",
        channel="chat",
        core_client=core_client,
        crm_client=crm_client,
        notify_client=notify_client,
    )

    result = await graph.ainvoke(state)

    logger.info("Test 2 Results:")
    logger.info(f"  Intent: {result.get('intent')}")
    logger.info(f"  Workflow: {result.get('workflow_name')}")
    logger.info(f"  Status: {result.get('result', {}).get('status')}")
    logger.info(f"  Response: {result.get('final_response')[:100]}...")
    
    assert result.get('intent') == 'unknown', "Intent should be unknown"
    assert result.get('workflow_name') == 'fallback_workflow', "Should route to fallback_workflow"
    assert result.get('result', {}).get('status') == 'fallback', "Should have fallback status"
    
    print("✅ Test 2 PASSED: Unknown intent routed to fallback\n")


async def test_statement_request_routing():
    """Test that statement requests route to fallback (until statement workflow is implemented)"""
    logger.info("=" * 60)
    logger.info("TEST 3: Statement Request Routing (Not Yet Implemented)")
    logger.info("=" * 60)
    
    core_client = CoreBankingClient(base_url=MOCK_SERVICES_BASE_URL)
    crm_client = CRMClient(base_url=MOCK_SERVICES_BASE_URL)
    notify_client = NotificationClient(base_url=MOCK_SERVICES_BASE_URL)

    graph = get_master_router_graph()
    
    state = get_initial_state(
        user_message="I need my last 3 months of bank statements",
        customer_id="cust789",
        channel="mobile",
        core_client=core_client,
        crm_client=crm_client,
        notify_client=notify_client,
    )

    result = await graph.ainvoke(state)

    logger.info("Test 3 Results:")
    logger.info(f"  Intent: {result.get('intent')}")
    logger.info(f"  Workflow: {result.get('workflow_name')}")
    logger.info(f"  Status: {result.get('result', {}).get('status')}")
    
    # Should route to fallback since statement_workflow not implemented
    assert result.get('intent') == 'request_statement', "Intent should be request_statement"
    assert result.get('workflow_name') == 'fallback_workflow', "Should route to fallback until statement_workflow is implemented"
    assert result.get('result', {}).get('status') == 'fallback', "Should have fallback status"
    
    print("✅ Test 3 PASSED: Unimplemented workflow routed to fallback\n")


async def main():
    print("\n" + "=" * 60)
    print("MASTER ROUTER GRAPH TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        await test_address_update_routing()
        await test_unknown_intent_routing()
        await test_statement_request_routing()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
