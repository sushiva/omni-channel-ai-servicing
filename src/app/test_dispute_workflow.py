"""
Test script for the dispute resolution workflow.

Tests that dispute requests are properly routed and processed.
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.app.config.settings import MOCK_SERVICES_BASE_URL
from src.graph.registry import get_master_router_graph, get_initial_state
from src.integrations.core_banking_client import CoreBankingClient
from src.integrations.crm_client import CRMClient
from src.integrations.notification_client import NotificationClient
from src.integrations.workflow_client import WorkflowClient
from src.monitoring.logger import get_logger

logger = get_logger("test_dispute_workflow")


async def test_dispute_routing():
    """Test that dispute requests route to dispute_workflow"""
    logger.info("=" * 60)
    logger.info("TEST: Dispute Transaction Routing")
    logger.info("=" * 60)
    
    core_client = CoreBankingClient(base_url=MOCK_SERVICES_BASE_URL)
    crm_client = CRMClient(base_url=MOCK_SERVICES_BASE_URL)
    notify_client = NotificationClient(base_url=MOCK_SERVICES_BASE_URL)
    workflow_client = WorkflowClient(base_url=MOCK_SERVICES_BASE_URL)

    # Get master router graph
    graph = get_master_router_graph()
    
    # Create state with dispute request
    state = get_initial_state(
        user_message="I want to dispute a charge of $250 from MegaMart on transaction TXN-12345. I didn't authorize this purchase.",
        customer_id="cust456",
        channel="chat",
        core_client=core_client,
        crm_client=crm_client,
        notify_client=notify_client,
        workflow_client=workflow_client,
    )

    result = await graph.ainvoke(state)

    logger.info("Dispute Test Results:")
    logger.info(f"  Intent: {result.get('intent')}")
    logger.info(f"  Workflow: {result.get('workflow_name')}")
    logger.info(f"  Case ID: {result.get('case_id')}")
    logger.info(f"  Status: {result.get('result', {}).get('status')}")
    logger.info(f"  Response: {result.get('final_response')[:100]}...")
    
    assert result.get('intent') == 'dispute_transaction', "Intent should be dispute_transaction"
    assert result.get('workflow_name') == 'dispute_workflow', "Should route to dispute_workflow"
    assert result.get('case_id') is not None, "Should create a case ID"
    
    print("✅ Dispute workflow test PASSED!\n")
    return result


async def main():
    print("\n" + "=" * 60)
    print("DISPUTE RESOLUTION WORKFLOW TEST")
    print("=" * 60 + "\n")
    
    try:
        result = await test_dispute_routing()
        
        print("=" * 60)
        print("✅ DISPUTE WORKFLOW IMPLEMENTED & TESTED")
        print("=" * 60)
        print(f"\nCase created: {result.get('case_id')}")
        print(f"Final response: {result.get('final_response')}\n")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
