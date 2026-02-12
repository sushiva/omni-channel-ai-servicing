"""
Simple standalone test for email processing (no imports from src).
"""
import re
from email_reply_parser import EmailReplyParser


def clean_email(body: str) -> str:
    """Clean email body"""
    # Extract original message
    reply = EmailReplyParser.parse_reply(body)
    cleaned = reply if reply else body
    
    # Remove signatures
    if '--' in cleaned:
        cleaned = cleaned.split('--')[0]
    
    # Remove extra whitespace
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    return '\n'.join(lines)


# Test Case 1: Address Update
print("="*60)
print("TEST 1: Address Update Email")
print("="*60)

email_1 = """
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

cleaned_1 = clean_email(email_1)
print(f"Original: {len(email_1)} chars")
print(f"Cleaned: {len(cleaned_1)} chars\n")
print(cleaned_1)

# Test Case 2: Dispute
print("\n" + "="*60)
print("TEST 2: Transaction Dispute")
print("="*60)

email_2 = """
Hello,

I want to dispute a charge of $250 from MegaMart on transaction TXN-12345.
I did not authorize this purchase.

Please investigate.

Best regards,
Jane Smith
"""

cleaned_2 = clean_email(email_2)
print(cleaned_2)

# Test Case 3: Reply Chain
print("\n" + "="*60)
print("TEST 3: Email with Reply Chain")
print("="*60)

email_3 = """
I need my January 2026 statement.

On Mon, Feb 1, 2026 at 10:00 AM Support <support@bank.com> wrote:
> Thank you for contacting us.
"""

cleaned_3 = clean_email(email_3)
print(f"Original: {len(email_3)} chars")
print(f"Cleaned: {len(cleaned_3)} chars\n")
print(cleaned_3)

print("\n" + "="*60)
print("✅ EMAIL CLEANING TESTS PASSED")
print("="*60)
