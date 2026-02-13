"""
SMTP email sender for sending responses to customers.

Uses Gmail SMTP to send email replies.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """
    SMTP client for sending email responses.
    
    Uses TLS (port 587) for secure email sending.
    """
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_name: str = "Customer Support"
    ):
        """
        Initialize SMTP email sender.
        
        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (587 for TLS)
            username: Email username
            password: Email password (app password for Gmail)
            from_name: Display name for sender
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.from_email = username
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body
            in_reply_to: Optional Message-ID this is replying to (for threading)
            references: Optional References header for email threading
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add threading headers for proper email threading
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
            if references:
                msg['References'] = references
            elif in_reply_to:
                msg['References'] = in_reply_to
            
            # Attach plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Attach HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                # Enable TLS encryption
                server.starttls()
                
                # Login
                logger.debug(f"Logging in as {self.username}")
                server.login(self.username, self.password)
                
                # Send email
                logger.info(f"Sending email to {to_email}: {subject}")
                server.send_message(msg)
                
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            logger.error("Make sure you're using an App Password, not your regular Gmail password")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False
    
    def send_response(
        self,
        to_email: str,
        original_subject: str,
        response_text: str,
        original_message_id: Optional[str] = None
    ) -> bool:
        """
        Send a response email to a customer request.
        
        This is a convenience method that handles common response patterns:
        - Adds "Re: " prefix to subject if not already present
        - Sets up proper email threading headers
        - Uses a professional email template
        
        Args:
            to_email: Customer email address
            original_subject: Subject of the original email
            response_text: Response message to send
            original_message_id: Message-ID of original email (for threading)
            
        Returns:
            True if email sent successfully
        """
        # Add "Re: " prefix if not present
        if not original_subject.lower().startswith('re:'):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject
        
        # Format response with professional template
        body = self._format_response_body(response_text)
        html_body = self._format_response_html(response_text)
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            in_reply_to=original_message_id,
            references=original_message_id
        )
    
    def _format_response_body(self, response_text: str) -> str:
        """Format plain text response body"""
        return f"""Hello,

{response_text}

If you have any further questions, please don't hesitate to reach out.

Best regards,
Customer Support Team

---
This is an automated response from our AI-powered customer service system.
"""
    
    def _format_response_html(self, response_text: str) -> str:
        """Format HTML response body"""
        # Convert newlines to <br> tags
        response_html = response_text.replace('\n', '<br>')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Hello,</p>
    
    <p>{response_html}</p>
    
    <p>If you have any further questions, please don't hesitate to reach out.</p>
    
    <p>Best regards,<br>
    <strong>Customer Support Team</strong></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">
        This is an automated response from our AI-powered customer service system.
    </p>
</body>
</html>
"""
