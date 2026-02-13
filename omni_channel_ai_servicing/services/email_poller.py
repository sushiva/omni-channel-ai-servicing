"""
Email polling service.

Continuously monitors inbox for new emails and processes them through the workflow API.
"""
import asyncio
import logging
import httpx
from typing import Optional
from datetime import datetime

from omni_channel_ai_servicing.services.email_config import EmailConfig
from omni_channel_ai_servicing.integrations.email_client import EmailClient, EmailMessage
from omni_channel_ai_servicing.services.email_processor import EmailProcessor
from omni_channel_ai_servicing.integrations.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format='{"level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "timestamp": "%(asctime)s"}'
)
logger = logging.getLogger(__name__)


class EmailPoller:
    """
    Email polling service that monitors inbox and forwards to API.
    
    Flow:
    1. Connect to IMAP server
    2. Fetch unread emails
    3. Clean and process email content
    4. POST to API endpoint
    5. Mark as read or move to processed folder
    6. Wait and repeat
    """
    
    def __init__(self):
        self.config = EmailConfig
        self.email_client: Optional[EmailClient] = None
        self.email_sender: Optional[EmailSender] = None
        self.processor = EmailProcessor()
        self.running = False
        
    async def start(self):
        """Start the email polling service"""
        try:
            # Validate configuration
            self.config.validate()
            
            logger.info("="*60)
            logger.info("EMAIL POLLER SERVICE STARTING")
            logger.info("="*60)
            logger.info(f"IMAP Server: {self.config.IMAP_HOST}:{self.config.IMAP_PORT}")
            logger.info(f"Username: {self.config.USERNAME}")
            logger.info(f"Mailbox: {self.config.MAILBOX}")
            logger.info(f"Poll Interval: {self.config.POLL_INTERVAL}s")
            logger.info(f"API Endpoint: {self.config.API_BASE_URL}/api/v1/service-request")
            logger.info("="*60)
            
            # Create email client
            self.email_client = EmailClient(
                host=self.config.IMAP_HOST,
                port=self.config.IMAP_PORT,
                username=self.config.USERNAME,
                password=self.config.PASSWORD,
                mailbox=self.config.MAILBOX
            )
            
            # Connect to email server
            self.email_client.connect()
            logger.info("✅ Connected to email server (IMAP)")
            
            # Create email sender (SMTP)
            self.email_sender = EmailSender(
                smtp_host=self.config.SMTP_HOST,
                smtp_port=self.config.SMTP_PORT,
                username=self.config.USERNAME,
                password=self.config.PASSWORD,
                from_name=self.config.FROM_NAME
            )
            logger.info("✅ Email sender initialized (SMTP)")
            
            # Handle existing unread emails
            if self.config.SKIP_EXISTING_ON_STARTUP:
                logger.info("⏭️  Skipping existing unread emails (will only process new arrivals)")
                # Mark all existing as seen without processing
                existing_emails = self.email_client.fetch_unread_emails(limit=100)
                if existing_emails:
                    existing_uids = [email.uid for email in existing_emails]
                    self.email_client.mark_as_read(existing_uids)
                    logger.info(f"Marked {len(existing_uids)} existing email(s) as read")
            
            # Start polling loop
            self.running = True
            await self._poll_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start email poller: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the email polling service"""
        self.running = False
        if self.email_client:
            self.email_client.disconnect()
            logger.info("Email poller stopped")
    
    async def _poll_loop(self):
        """Main polling loop"""
        logger.info(f"🔄 Starting poll loop (checking every {self.config.POLL_INTERVAL}s)")
        
        while self.running:
            try:
                await self._poll_once()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                # Continue polling even if one iteration fails
            
            # Wait before next poll
            await asyncio.sleep(self.config.POLL_INTERVAL)
    
    async def _poll_once(self):
        """Perform one poll iteration"""
        try:
            # Fetch unread emails
            emails = self.email_client.fetch_unread_emails(limit=10)
            
            if not emails:
                logger.debug("No new emails")
                return
            
            logger.info(f"📧 Processing {len(emails)} new email(s)")
            
            # Process each email
            processed_uids = []
            for email_msg in emails:
                try:
                    success = await self._process_email(email_msg)
                    if success:
                        processed_uids.append(email_msg.uid)
                except Exception as e:
                    logger.error(f"Failed to process email {email_msg.uid}: {e}")
            
            # Mark processed emails as read
            if processed_uids and self.config.MARK_AS_READ:
                self.email_client.mark_as_read(processed_uids)
            
            logger.info(f"✅ Processed {len(processed_uids)}/{len(emails)} email(s)")
            
        except Exception as e:
            logger.error(f"Error during poll: {e}")
            raise
    
    async def _process_email(self, email_msg: EmailMessage) -> bool:
        """
        Process a single email message.
        
        Args:
            email_msg: EmailMessage to process
            
        Returns:
            True if successfully processed
        """
        try:
            logger.info(f"Processing email from {email_msg.sender}: {email_msg.subject[:50]}")
            
            # Check if we should process this email
            if not self.processor.should_process_email(
                email_msg.sender,
                email_msg.subject,
                email_msg.to_address
            ):
                logger.info("Skipping email (not sent to support or auto-reply)")
                return False
            
            # Clean email body
            cleaned_body = self.processor.clean_email_body(email_msg.body)
            
            if not cleaned_body.strip():
                logger.warning("Email body is empty after cleaning, skipping")
                return False
            
            # Extract sender email
            sender_email = self.processor.extract_customer_email(email_msg.sender)
            
            # Look up customer ID (you can enhance this with CRM lookup)
            customer_id = await self._lookup_customer_id(sender_email)
            
            # Create API payload
            payload = self.processor.create_api_payload(
                cleaned_body=cleaned_body,
                sender=sender_email,
                subject=email_msg.subject,
                message_id=email_msg.message_id,
                customer_id=customer_id
            )
            
            logger.info(f"Sending to API: customer_id={customer_id}, message_length={len(cleaned_body)}")
            logger.debug(f"Message preview: {cleaned_body[:200]}")
            
            # Send to API
            response = await self._send_to_api(payload)
            
            if response:
                logger.info(f"✅ Email processed successfully: {response.get('status')}")
                
                # Send email response back to customer
                await self._send_email_response(
                    to_email=sender_email,
                    subject=f"Re: {email_msg.subject}",
                    body=response.get('response', 'Your request has been processed.'),
                    in_reply_to=email_msg.message_id
                )
                
                return True
            else:
                logger.warning("API returned no response")
                return False
                
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return False
    
    async def _lookup_customer_id(self, email_address: str) -> str:
        """
        Look up customer ID from email address.
        
        TODO: Integrate with CRM API to get real customer ID
        
        Args:
            email_address: Customer email address
            
        Returns:
            Customer ID
        """
        # For now, use email as customer ID
        # In production, this would call CRM API
        return f"EMAIL-{email_address}"
    
    async def _send_to_api(self, payload: dict) -> Optional[dict]:
        """
        Send email data to workflow API.
        
        Args:
            payload: API request payload
            
        Returns:
            API response or None if failed
        """
        url = f"{self.config.API_BASE_URL}/api/v1/service-request"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling API: {e}")
            return None
    
    async def _send_email_response(
        self,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None
    ):
        """
        Send email response back to customer via SMTP.
        
        Args:
            to_email: Customer email address
            subject: Email subject (original subject from customer)
            body: Response message
            in_reply_to: Original message ID for email threading
        """
        try:
            logger.info(f"📤 Sending email response to {to_email}")
            logger.debug(f"Subject: Re: {subject}")
            logger.debug(f"Body preview: {body[:200]}")
            
            # Send email via SMTP (sync call wrapped for async context)
            import asyncio
            success = await asyncio.to_thread(
                self.email_sender.send_response,
                to_email=to_email,
                original_subject=subject,
                response_text=body,
                original_message_id=in_reply_to
            )

            if success:
                logger.info(f"✅ Email response sent successfully to {to_email}")
            else:
                logger.warning(f"Failed to send email response to {to_email}")

        except Exception as e:
            logger.error(f"Error sending email response: {e}")


async def main():
    """Main entry point for email poller service"""
    poller = EmailPoller()
    
    try:
        await poller.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down email poller...")
        await poller.stop()
    except Exception as e:
        logger.error(f"❌ Email poller failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
