#!/usr/bin/env python3
"""
Test email channel with document verification scenario.

Simulates a customer emailing to update their address with attached documents.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from omni_channel_ai_servicing.integrations import create_clients
from omni_channel_ai_servicing.graph.registry import get_master_router_graph, get_initial_state


async def test_email_with_documents():
    """
    Test email channel with customer providing documents.
    
    Scenario: Customer emails saying they want to update their address
    and mentions they have attached required documents (ID, proof of address).
    """
    print("="*80)
    print("EMAIL CHANNEL TEST - Address Update with Documents")
    print("="*80)
    
    try:
        # Create clients and graph
        print("\n✓ Creating integration clients...")
        clients = create_clients()
        
        print("✓ Building master router graph...")
        graph = get_master_router_graph()
        
        # Simulate email from customer
        email_body = """
Hi,

I recently moved to a new address and need to update my mailing address on my account.

My new address is:
123 Main Street, Apt 4B
San Francisco, CA 94102

I have attached copies of my driver's license and a recent utility bill as proof of my new address.

Please let me know if you need any additional information.

Thank you,
John Smith
        """
        
        # Create state with email channel
        state = get_initial_state(
            user_message=email_body.strip(),
            customer_id="john.smith@example.com",
            channel="email",
            metadata={
                "email_sender": "john.smith@example.com",
                "email_subject": "Address Update - Documents Attached",
                "email_message_id": "<test-123@example.com>",
                "has_attachments": True,
                "attachments": [
                    "drivers_license.pdf",
                    "utility_bill_nov_2025.pdf"
                ]
            },
            crm_client=clients.get("crm_client"),
            core_client=clients.get("core_client"),
            notify_client=clients.get("notify_client"),
            workflow_client=clients.get("workflow_client"),
        )
        
        print("\n✓ Created email channel state")
        print(f"  - Customer: {state.customer_id}")
        print(f"  - Channel: {state.channel}")
        print(f"  - Has attachments: Yes (2 files)")
        print(f"  - Trace ID: {state.trace_id}")
        
        print("\n" + "-"*80)
        print("Executing workflow...")
        print("-"*80 + "\n")
        
        # Execute graph
        result = await graph.ainvoke(state)
        
        # Display results
        print("\n" + "="*80)
        print("RESULTS:")
        print("="*80)
        
        print(f"\nIntent: {result.get('intent')}")
        print(f"Workflow: {result.get('workflow_name')}")
        print(f"Status: {result.get('result', {}).get('status', 'N/A')}")
        
        context_metadata = result.get('context_metadata')
        if context_metadata:
            print(f"Retrieved Docs: {context_metadata.get('num_documents', 0)}")
        
        print(f"\nFinal Response:")
        print("-"*80)
        response = result.get('final_response', 'No response')
        print(response)
        print("-"*80)
        
        # Show retrieved documents
        retrieved_documents = result.get('retrieved_documents')
        if retrieved_documents:
            print(f"\n📚 Retrieved Documents ({len(retrieved_documents)}):")
            for i, doc in enumerate(retrieved_documents[:2], 1):
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                source = metadata.get('source', 'Unknown')
                content_preview = doc.content[:150] if hasattr(doc, 'content') else str(doc)[:150]
                print(f"\n  Document {i}:")
                print(f"  Source: {source}")
                print(f"  Preview: {content_preview}...")
        
        # Show extracted entities
        entities = result.get('entities', {})
        if entities:
            print(f"\n📋 Extracted Entities:")
            for key, value in entities.items():
                print(f"  - {key}: {value}")
        
        print("\n" + "="*80)
        print("✓ Email channel test completed successfully!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_without_documents():
    """
    Test email channel where customer forgot to attach documents.
    
    System should ask for required documents.
    """
    print("\n" + "="*80)
    print("EMAIL CHANNEL TEST - Address Update WITHOUT Documents")
    print("="*80)
    
    try:
        clients = create_clients()
        graph = get_master_router_graph()
        
        # Email without mention of documents
        email_body = """
Hi,

I need to update my address. My new address is 123 Main St, SF, CA 94102.

Thanks!
        """
        
        state = get_initial_state(
            user_message=email_body.strip(),
            customer_id="jane.doe@example.com",
            channel="email",
            metadata={
                "email_sender": "jane.doe@example.com",
                "email_subject": "Update Address",
                "email_message_id": "<test-456@example.com>",
                "has_attachments": False
            },
            crm_client=clients.get("crm_client"),
            core_client=clients.get("core_client"),
            notify_client=clients.get("notify_client"),
            workflow_client=clients.get("workflow_client"),
        )
        
        print(f"\n✓ Testing email WITHOUT attachments")
        
        result = await graph.ainvoke(state)
        
        print(f"\nIntent: {result.get('intent')}")
        print(f"\nResponse Preview:")
        print("-"*80)
        response = result.get('final_response', '')
        print(response[:500] + "..." if len(response) > 500 else response)
        print("-"*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


async def main():
    """Run all email channel tests"""
    print("\n" + "="*80)
    print("EMAIL CHANNEL INTEGRATION TESTS")
    print("="*80)
    
    success1 = await test_email_with_documents()
    success2 = await test_email_without_documents()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Email with documents: {'✓ PASS' if success1 else '✗ FAIL'}")
    print(f"Email without documents: {'✓ PASS' if success2 else '✗ FAIL'}")
    print("="*80 + "\n")
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
