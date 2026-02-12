"""
Test email integration without connecting to real email server.

Tests the email processing pipeline with mock data.
"""
import asyncio
import logging
from omni_channel_ai_servicing.services.email_processor import EmailProcessor
from omni_channel_ai_servicing.integrations.email_client import EmailMessage
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_email_processing():
    """Test email processing with mock data"""
    
    processor = EmailProcessor()
    
    # Test Case 1: Address Update Email
    print("\n" + "="*60)
    print("TEST 1: Address Update Email")
    print("="*60)
    
    email_body_1 = """
Hi Support Team,

I need to update my mailing address. My new address is:
123 Oak Street
Austin, TX 78701

Please update your records.

Thanks,
John Doe

--
Sent from my iPhone
    """
    
    cleaned_1 = processor.clean_email_body(email_body_1)
    print(f"Original length: {len(email_body_1)}")
    print(f"Cleaned length: {len(cleaned_1)}")
    print(f"\nCleaned text:\n{cleaned_1}")
    
    payload_1 = processor.create_api_payload(
        cleaned_body=cleaned_1,
        sender="john.doe@example.com",
        subject="Address Update Request",
        message_id="<msg-001@example.com>",
        customer_id="CUST-12345"
    )
    print(f"\nAPI Payload:")
    print(f"  customer_id: {payload_1['customer_id']}")
    print(f"  channel: {payload_1['channel']}")
    print(f"  message: {payload_1['user_message'][:100]}...")
    
    # Test Case 2: Dispute Email
    print("\n" + "="*60)
    print("TEST 2: Transaction Dispute Email")
    print("="*60)
    
    email_body_2 = """
Hello,

I want to dispute a charge of $250 from MegaMart on transaction TXN-12345.
I did not authorize this purchase and I never received the items.

Please investigate this immediately.

Best regards,
Jane Smith
    """
    
    cleaned_2 = processor.clean_email_body(email_body_2)
    print(f"Cleaned text:\n{cleaned_2}")
    
    # Test Case 3: Email with Reply Chain
    print("\n" + "="*60)
    print("TEST 3: Email with Reply Chain (Should Strip)")
    print("="*60)
    
    email_body_3 = """
I need my January 2026 statement.

On Mon, Feb 1, 2026 at 10:00 AM Support <support@bank.com> wrote:
> Thank you for contacting us. How can we help?

> --
> Customer Service Team
> Bank of Example
    """
    
    cleaned_3 = processor.clean_email_body(email_body_3)
    print(f"Original length: {len(email_body_3)}")
    print(f"Cleaned length: {len(cleaned_3)}")
    print(f"\nCleaned text:\n{cleaned_3}")
    
    # Test Case 4: Auto-Reply Detection
    print("\n" + "="*60)
    print("TEST 4: Auto-Reply Detection")
    print("="*60)
    
    test_cases = [
        ("noreply@bank.com", "Welcome to our service", False),
        ("john@example.com", "Out of Office", False),
        ("jane@example.com", "I need help", True),
        ("automated-system@bank.com", "Transaction alert", False),
    ]
    
    for sender, subject, expected in test_cases:
        result = processor.should_process_email(sender, subject)
        status = "✅" if result == expected else "❌"
        print(f"{status} Sender: {sender:30} Subject: {subject:30} Process: {result}")
    
    print("\n" + "="*60)
    print("✅ EMAIL PROCESSING TESTS COMPLETE")
    print("="*60)


async def test_email_client_mock():
    """Test email client with mock message"""
    print("\n" + "="*60)
    print("EMAIL CLIENT MOCK TEST")
    print("="*60)
    
    # Create a mock email message
    mock_email = EmailMessage(
        message_id="<test-123@example.com>",
        uid=1,
        subject="Need help with my account",
        sender="customer@example.com",
        body="I want to update my address to 456 Pine St, Dallas TX 75201",
        received_at=datetime.now()
    )
    
    print(f"Mock Email:")
    print(f"  From: {mock_email.sender}")
    print(f"  Subject: {mock_email.subject}")
    print(f"  Body: {mock_email.body}")
    
    processor = EmailProcessor()
    cleaned = processor.clean_email_body(mock_email.body)
    
    payload = processor.create_api_payload(
        cleaned_body=cleaned,
        sender=mock_email.sender,
        subject=mock_email.subject,
        message_id=mock_email.message_id
    )
    
    print(f"\nReady for API:")
    print(f"  Payload: {payload}")
    print("\n✅ Mock test complete")


async def main():
    """Run all tests"""
    await test_email_processing()
    await test_email_client_mock()


if __name__ == "__main__":
    asyncio.run(main())
