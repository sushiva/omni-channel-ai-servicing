"""
Email IDLE service using IMAP IDLE for push notifications.

Instead of polling every 30s, this uses IMAP IDLE to get instant notifications
when new emails arrive. Much more efficient and responsive.
"""
import asyncio
import logging
import httpx
from typing import Optional
from datetime import datetime
import threading

from omni_channel_ai_servicing.services.email_config import EmailConfig
from omni_channel_ai_servicing.integrations.email_client import EmailClient, EmailMessage
from omni_channel_ai_servicing.services.email_processor import EmailProcessor
from omni_channel_ai_servicing.integrations.email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format='{"level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "timestamp": "%(asctime)s"}'
)
logger = logging.getLogger(__name__)


class EmailIdlePoller:
    """
    Email service using IMAP IDLE for push notifications.
    
    IMAP IDLE vs Polling:
    - Polling: Check every 30s (wastes resources, 30s delay)
    - IDLE: Server notifies immediately (efficient, instant)
    
    Flow:
    1. Connect to IMAP server
    2. Start IDLE mode (server will notify on new mail)
    3. When notification arrives, fetch new emails
    4. Process emails through API
    5. Return to IDLE mode
    """
    
    def __init__(self):
        self.config = EmailConfig
        self.email_client: Optional[EmailClient] = None
        self.email_sender: Optional[EmailSender] = None
        self.processor = EmailProcessor()
        self.running = False
        self._idle_thread = None
        
    async def start(self):
        """Start the email IDLE service"""
        try:
            # Validate configuration
            self.config.validate()
            
            logger.info("="*60)
            logger.info("EMAIL IDLE SERVICE STARTING")
            logger.info("="*60)
            logger.info(f"IMAP Server: {self.config.IMAP_HOST}:{self.config.IMAP_PORT}")
            logger.info(f"Username: {self.config.USERNAME}")
            logger.info(f"Mailbox: {self.config.MAILBOX}")
            logger.info(f"Mode: IMAP IDLE (push notifications)")
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
            
            # Process existing unread emails (or skip them)
            if self.config.SKIP_EXISTING_ON_STARTUP:
                logger.info("⏭️  Skipping existing unread emails (will only process new arrivals)")
                # Mark all existing as seen without processing
                existing_emails = self.email_client.fetch_unread_emails(limit=100)
                if existing_emails:
                    existing_uids = [email.uid for email in existing_emails]
                    self.email_client.mark_as_read(existing_uids)
                    logger.info(f"Marked {len(existing_uids)} existing email(s) as read")
            else:
                logger.info("🔍 Processing existing unread emails...")
                await self._process_existing_emails()
            
            # Start IDLE loop
            self.running = True
            await self._idle_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start email IDLE service: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the email IDLE service"""
        self.running = False
        if self.email_client:
            try:
                # Stop IDLE if active
                if hasattr(self.email_client.client, 'idle_done'):
                    self.email_client.client.idle_done()
            except:
                pass
            self.email_client.disconnect()
            logger.info("Email IDLE service stopped")
    
    async def _process_existing_emails(self):
        """Process any unread emails that exist before starting IDLE"""
        try:
            emails = self.email_client.fetch_unread_emails(limit=10)
            if emails:
                logger.info(f"📧 Found {len(emails)} existing unread email(s)")
                await self._process_emails(emails)
            else:
                logger.info("No existing unread emails")
        except Exception as e:
            logger.error(f"Error processing existing emails: {e}")
    
    async def _idle_loop(self):
        """
        Main IDLE loop using IMAP IDLE.
        
        IMAP IDLE protocol:
        1. Send IDLE command
        2. Server sends notifications when new mail arrives
        3. Exit IDLE, process emails
        4. Return to IDLE
        
        Gmail auto-disconnects IDLE after 29 minutes, so we restart every 20 minutes.
        """
        logger.info("🔔 Starting IDLE mode - waiting for new emails...")
        
        while self.running:
            try:
                # Start IDLE mode (timeout after 20 minutes to refresh connection)
                # Gmail's IDLE timeout is 29 minutes, so we use 20 to be safe
                timeout_seconds = 20 * 60  # 20 minutes
                
                logger.debug(f"Entering IDLE mode (timeout: {timeout_seconds}s)...")
                
                # Start IDLE in a separate thread to avoid blocking
                responses = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._idle_check,
                    timeout_seconds
                )
                
                # Check if we got notifications
                if responses:
                    logger.info("📬 New email notification received!")
                    
                    # Fetch and process new emails
                    await self._fetch_and_process()
                    
                else:
                    # Timeout reached, just refresh connection
                    logger.debug("IDLE timeout reached, refreshing connection...")
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in IDLE loop: {e}")
                # Wait a bit before retrying to avoid tight loop on persistent errors
                await asyncio.sleep(5)
                
                # Try to reconnect
                try:
                    logger.info("Attempting to reconnect...")
                    self.email_client.disconnect()
                    self.email_client.connect()
                    logger.info("✅ Reconnected successfully")
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect: {reconnect_error}")
                    await asyncio.sleep(30)  # Wait longer before retry
    
    def _idle_check(self, timeout: int):
        """
        Perform IDLE check (blocking call, runs in thread).
        
        Args:
            timeout: How long to wait in seconds
            
        Returns:
            List of responses from server, or None if timeout
        """
        try:
            # Start IDLE
            self.email_client.client.idle()
            
            # Wait for notifications (blocking)
            # idle_check() returns responses or empty list on timeout
            responses = self.email_client.client.idle_check(timeout=timeout)
            
            # Stop IDLE
            self.email_client.client.idle_done()
            
            return responses
            
        except Exception as e:
            logger.error(f"Error in IDLE check: {e}")
            try:
                self.email_client.client.idle_done()
            except:
                pass
            return None
    
    async def _fetch_and_process(self):
        """Fetch new unread emails and process them"""
        try:
            # Fetch unread emails
            emails = self.email_client.fetch_unread_emails(limit=10)
            
            if not emails:
                logger.debug("No new emails to process")
                return
            
            logger.info(f"📧 Processing {len(emails)} new email(s)")
            await self._process_emails(emails)
            
        except Exception as e:
            logger.error(f"Error fetching/processing emails: {e}")
    
    async def _process_emails(self, emails: list[EmailMessage]):
        """Process a list of emails"""
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
                
                # Send email response back to customer (TODO: implement SMTP)
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
    
    async def _lookup_customer_id(self, email: str) -> str:
        """
        Look up customer ID from email address.
        
        TODO: Integrate with CRM system for real customer lookup.
        For now, use email as customer ID.
        """
        # In production, this would call a CRM API:
        # customer = await crm_client.get_customer_by_email(email)
        # return customer.id
        
        return f"EMAIL-{email}"
    
    async def _send_to_api(self, payload: dict) -> Optional[dict]:
        """
        Send processed email to API endpoint.
        
        Args:
            payload: Request payload
            
        Returns:
            API response dict or None if failed
        """
        try:
            url = f"{self.config.API_BASE_URL}/api/v1/service-request"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.debug(f"API response: {result}")
                return result
                
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
    """Main entry point"""
    poller = EmailIdlePoller()
    try:
        await poller.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await poller.stop()


if __name__ == "__main__":
    asyncio.run(main())
