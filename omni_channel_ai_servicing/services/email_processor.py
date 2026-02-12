"""
Email preprocessing and cleaning.

Handles email signature removal, reply chain stripping, and text cleaning.
"""
import logging
import os
import re
from typing import Optional
from email_reply_parser import EmailReplyParser

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Process and clean email content for workflow processing"""
    
    # Common signature patterns
    SIGNATURE_PATTERNS = [
        r'--\s*\n',  # Standard signature delimiter
        r'Sent from my (?:iPhone|iPad|Android)',
        r'Best regards?,',
        r'Thanks?,',
        r'Sincerely,',
        r'Regards,',
    ]
    
    # Patterns to remove
    NOISE_PATTERNS = [
        r'On .+ wrote:',  # Reply headers
        r'>.*',  # Quoted text
        r'_{10,}',  # Long underscores
        r'-{10,}',  # Long dashes
    ]
    
    def __init__(self):
        pass
    
    def clean_email_body(self, body: str) -> str:
        """
        Clean email body text for processing.
        
        Steps:
        1. Extract original message (remove quotes/replies)
        2. Remove signatures
        3. Remove extra whitespace
        4. Remove noise patterns
        
        Args:
            body: Raw email body text
            
        Returns:
            Cleaned email text
        """
        if not body:
            return ""
        
        try:
            # Step 1: Use email-reply-parser to extract original message
            reply = EmailReplyParser.parse_reply(body)
            cleaned = reply if reply else body
            
            # Step 2: Remove signatures
            cleaned = self._remove_signatures(cleaned)
            
            # Step 3: Remove noise patterns
            cleaned = self._remove_noise(cleaned)
            
            # Step 4: Clean whitespace
            cleaned = self._clean_whitespace(cleaned)
            
            logger.debug(f"Cleaned email: {len(body)} -> {len(cleaned)} chars")
            return cleaned
            
        except Exception as e:
            logger.warning(f"Failed to clean email body: {e}. Using original.")
            return self._clean_whitespace(body)
    
    def _remove_signatures(self, text: str) -> str:
        """Remove common email signatures"""
        for pattern in self.SIGNATURE_PATTERNS:
            # Find signature and remove everything after it
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                text = text[:match.start()]
        return text
    
    def _remove_noise(self, text: str) -> str:
        """Remove noise patterns like quoted text and separators"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip quoted lines (starting with >)
            if line.strip().startswith('>'):
                continue
            
            # Skip lines matching noise patterns
            skip = False
            for pattern in self.NOISE_PATTERNS:
                if re.search(pattern, line):
                    skip = True
                    break
            
            if not skip:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace"""
        # Replace multiple newlines with max 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing/leading whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Remove empty lines at start and end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)
    
    def extract_customer_email(self, sender: str) -> str:
        """
        Extract clean email address from sender field.
        
        Args:
            sender: Email sender (e.g., "John Doe <john@example.com>")
            
        Returns:
            Clean email address
        """
        # Already clean
        if '@' in sender and '<' not in sender:
            return sender.lower().strip()
        
        # Extract from "Name <email>" format
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1).lower().strip()
        
        return sender.lower().strip()
    
    def should_process_email(self, sender: str, subject: str, to_address: Optional[str] = None) -> bool:
        """
        Determine if email should be processed.
        
        Filters out:
        - Emails not sent to support address (noise/newsletters)
        - Auto-replies
        - System notifications
        - Spam patterns
        
        Args:
            sender: Email sender address
            subject: Email subject line
            to_address: Recipient address (who the email was sent TO)
            
        Returns:
            True if email should be processed
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        
        # CRITICAL: Only process emails sent TO the support address
        # This filters out newsletters, personal emails, etc.
        if to_address:
            support_email = os.getenv('SUPPORT_EMAIL', 'support@bank.com').lower()
            # Also check common support email variations
            support_addresses = [
                support_email,
                os.getenv('EMAIL_USERNAME', '').lower(),  # The inbox itself
            ]
            
            to_lower = to_address.lower()
            is_to_support = any(addr in to_lower for addr in support_addresses if addr)
            
            if not is_to_support:
                logger.info(f"Skipping email not sent to support address (sent to: {to_address})")
                return False
        
        # Filter out auto-replies
        auto_reply_patterns = [
            'noreply',
            'no-reply',
            'donotreply',
            'mailer-daemon',
            'postmaster',
            'automated',
        ]

        for pattern in auto_reply_patterns:
            if pattern in sender_lower:
                logger.info(f"Skipping auto-reply from {sender}")
                return False

        # Filter out bulk/marketing email sender domains
        bulk_sender_domains = [
            'ccsend.com',        # Constant Contact
            'mailchimp.com',
            'sendgrid.net',
            'mailgun.org',
            'amazonses.com',
            'constantcontact.com',
            'campaign-archive.com',
            'list-manage.com',
            'hubspot.com',
            'marketo.com',
            'salesforce.com',
            'pardot.com',
            'mailerlite.com',
            'sendinblue.com',
            'brevo.com',
        ]

        for domain in bulk_sender_domains:
            if domain in sender_lower:
                logger.info(f"Skipping bulk/marketing email from {sender} (domain: {domain})")
                return False

        # Filter out auto-reply subjects
        auto_subject_patterns = [
            'out of office',
            'automatic reply',
            'auto-reply',
            'delivery failure',
            'undeliverable',
            'mail delivery failed',
        ]

        for pattern in auto_subject_patterns:
            if pattern in subject_lower:
                logger.info(f"Skipping auto-reply: {subject}")
                return False

        # Filter out marketing/newsletter subjects
        marketing_subject_patterns = [
            'unsubscribe',
            'newsletter',
            'subscribed',
            'promotional',
            'special offer',
            'limited time',
            'act now',
            'click here',
            'free trial',
        ]

        for pattern in marketing_subject_patterns:
            if pattern in subject_lower:
                logger.info(f"Skipping marketing email: {subject}")
                return False

        # All checks passed
        return True
    
    def create_api_payload(
        self,
        cleaned_body: str,
        sender: str,
        subject: str,
        message_id: str,
        customer_id: Optional[str] = None
    ) -> dict:
        """
        Create API payload for service request.
        
        Args:
            cleaned_body: Cleaned email body text
            sender: Sender email address
            subject: Email subject
            message_id: Email message ID
            customer_id: Customer ID (if known)
            
        Returns:
            API payload dict
        """
        return {
            "customer_id": customer_id or f"EMAIL-{sender}",
            "message": cleaned_body,
            "channel": "email",
            "metadata": {
                "email_sender": sender,
                "email_subject": subject,
                "email_message_id": message_id,
            }
        }
