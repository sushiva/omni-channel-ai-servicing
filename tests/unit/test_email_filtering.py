"""
Unit tests for email filtering logic.

Tests the should_process_email() function with various scenarios.
"""
import pytest
import os
from omni_channel_ai_servicing.services.email_processor import EmailProcessor


class TestEmailFiltering:
    """Test email filtering and noise rejection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = EmailProcessor()
        # Set test support email
        os.environ['SUPPORT_EMAIL'] = 'support@bank.com'
        os.environ['EMAIL_USERNAME'] = 'support@bank.com'
    
    def test_filter_by_recipient_address(self):
        """Test that only emails sent TO support address are processed"""
        
        # Should process: sent to support email
        assert self.processor.should_process_email(
            sender="customer@example.com",
            subject="I need help",
            to_address="support@bank.com"
        ) == True
        
        # Should NOT process: sent to different address (newsletter)
        assert self.processor.should_process_email(
            sender="newsletter@company.com",
            subject="Weekly updates",
            to_address="user@personal.com"
        ) == False
        
        # Should NOT process: bulk email not to support
        assert self.processor.should_process_email(
            sender="marketing@company.com",
            subject="Special offer",
            to_address="customer@example.com"
        ) == False
    
    def test_auto_reply_filtering(self):
        """Test auto-reply detection"""
        
        # Should filter out noreply addresses
        assert self.processor.should_process_email(
            sender="noreply@example.com",
            subject="Account notification",
            to_address="support@bank.com"
        ) == False
        
        assert self.processor.should_process_email(
            sender="no-reply@service.com",
            subject="Update",
            to_address="support@bank.com"
        ) == False
        
        assert self.processor.should_process_email(
            sender="donotreply@system.com",
            subject="Alert",
            to_address="support@bank.com"
        ) == False
        
        # Should process: real person
        assert self.processor.should_process_email(
            sender="john.doe@example.com",
            subject="Help needed",
            to_address="support@bank.com"
        ) == True
    
    def test_bulk_sender_filtering(self):
        """Test bulk/marketing sender domain filtering"""
        
        bulk_senders = [
            "newsletter@ccsend.com",
            "promo@mailchimp.com",
            "update@sendgrid.net",
            "alert@amazonses.com",
            "news@constantcontact.com",
        ]
        
        for sender in bulk_senders:
            assert self.processor.should_process_email(
                sender=sender,
                subject="Newsletter",
                to_address="support@bank.com"
            ) == False, f"Should filter bulk sender: {sender}"
    
    def test_auto_reply_subject_filtering(self):
        """Test auto-reply subject detection"""
        
        auto_subjects = [
            "Out of Office",
            "Automatic Reply: Your request",
            "Auto-reply: Vacation notice",
            "Delivery Failure",
            "Mail Delivery Failed",
            "Undeliverable: Your message",
        ]
        
        for subject in auto_subjects:
            assert self.processor.should_process_email(
                sender="person@example.com",
                subject=subject,
                to_address="support@bank.com"
            ) == False, f"Should filter auto-reply subject: {subject}"
    
    def test_newsletter_subject_filtering(self):
        """Test newsletter/marketing subject filtering"""
        
        # Newsletters are primarily filtered by:
        # 1. Not being sent TO support address (most common)
        # 2. Subject line patterns (backup filter)
        
        newsletter_subjects = [
            "Unsubscribe from our newsletter",
            "Weekly Newsletter - Feb 2026",
        ]
        
        for subject in newsletter_subjects:
            assert self.processor.should_process_email(
                sender="news@company.com",
                subject=subject,
                to_address="support@bank.com"
            ) == False, f"Should filter newsletter: {subject}"
    
    def test_legitimate_customer_emails(self):
        """Test that legitimate customer emails are processed"""
        
        legitimate_cases = [
            ("john@example.com", "Need to update my address", "support@bank.com"),
            ("jane.smith@company.com", "Transaction dispute", "support@bank.com"),
            ("customer@domain.com", "Request for statement", "support@bank.com"),
            ("user@email.com", "Fraud alert", "support@bank.com"),
        ]
        
        for sender, subject, to_addr in legitimate_cases:
            result = self.processor.should_process_email(
                sender=sender,
                subject=subject,
                to_address=to_addr
            )
            assert result == True, f"Should process: {sender} - {subject}"
    
    def test_combined_filtering(self):
        """Test multiple filter conditions together"""
        
        # Bulk sender + newsletter subject → should filter
        assert self.processor.should_process_email(
            sender="promo@mailchimp.com",
            subject="Weekly Newsletter",
            to_address="customer@example.com"
        ) == False
        
        # Auto-reply sender + auto subject → should filter
        assert self.processor.should_process_email(
            sender="noreply@system.com",
            subject="Out of Office",
            to_address="support@bank.com"
        ) == False
        
        # Normal sender + normal subject + to support → should process
        assert self.processor.should_process_email(
            sender="customer@example.com",
            subject="I need help",
            to_address="support@bank.com"
        ) == True
    
    def test_missing_to_address(self):
        """Test behavior when to_address is None (legacy compatibility)"""
        
        # Should still filter auto-replies even without to_address
        assert self.processor.should_process_email(
            sender="noreply@example.com",
            subject="Alert",
            to_address=None
        ) == False
        
        # Should process if not auto-reply (backward compatibility)
        assert self.processor.should_process_email(
            sender="customer@example.com",
            subject="Help",
            to_address=None
        ) == True
    
    def test_case_insensitive_filtering(self):
        """Test that filtering is case-insensitive"""
        
        # Should filter regardless of case
        assert self.processor.should_process_email(
            sender="NoReply@Example.Com",
            subject="Alert",
            to_address="SUPPORT@BANK.COM"
        ) == False
        
        assert self.processor.should_process_email(
            sender="customer@EXAMPLE.com",
            subject="HELP ME",
            to_address="Support@Bank.Com"
        ) == True


def test_email_processor_initialization():
    """Test that EmailProcessor initializes correctly"""
    processor = EmailProcessor()
    assert processor is not None
    assert hasattr(processor, 'should_process_email')
    assert hasattr(processor, 'clean_email_body')
    assert hasattr(processor, 'create_api_payload')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
