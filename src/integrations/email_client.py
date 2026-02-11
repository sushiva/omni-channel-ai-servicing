"""
Email client for reading emails via IMAP.

Handles connection, authentication, and email fetching.
"""
import logging
import email
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import imaplib
from imapclient import IMAPClient
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EmailMessage:
    """Represents a parsed email message"""
    
    def __init__(
        self,
        message_id: str,
        uid: int,
        subject: str,
        sender: str,
        body: str,
        received_at: datetime,
        html_body: Optional[str] = None,
        to_address: Optional[str] = None
    ):
        self.message_id = message_id
        self.uid = uid
        self.subject = subject
        self.sender = sender
        self.to_address = to_address
        self.body = body
        self.html_body = html_body
        self.received_at = received_at
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "uid": self.uid,
            "subject": self.subject,
            "sender": self.sender,
            "body": self.body,
            "received_at": self.received_at.isoformat()
        }


class EmailClient:
    """IMAP email client for reading emails"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        mailbox: str = "INBOX"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mailbox = mailbox
        self.client: Optional[IMAPClient] = None
    
    def connect(self) -> None:
        """Connect to IMAP server and authenticate"""
        try:
            logger.info(f"Connecting to {self.host}:{self.port}")
            self.client = IMAPClient(self.host, port=self.port, use_uid=True, ssl=True)
            self.client.login(self.username, self.password)
            self.client.select_folder(self.mailbox)
            logger.info(f"Successfully connected as {self.username}")
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from IMAP server"""
        if self.client:
            try:
                self.client.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.client = None
    
    def fetch_unread_emails(self, limit: int = 10) -> List[EmailMessage]:
        """
        Fetch unread emails from the mailbox.
        
        Args:
            limit: Maximum number of emails to fetch
            
        Returns:
            List of EmailMessage objects
        """
        if not self.client:
            raise RuntimeError("Not connected to email server. Call connect() first.")
        
        try:
            # Search for unseen messages
            message_ids = self.client.search(['UNSEEN'])
            
            if not message_ids:
                logger.debug("No unread emails found")
                return []
            
            # Limit the number of messages
            message_ids = message_ids[:limit]
            logger.info(f"Found {len(message_ids)} unread email(s)")
            
            # Fetch message data
            messages = []
            raw_messages = self.client.fetch(message_ids, ['RFC822', 'ENVELOPE'])
            
            for uid, data in raw_messages.items():
                try:
                    parsed = self._parse_message(uid, data)
                    if parsed:
                        messages.append(parsed)
                except Exception as e:
                    logger.error(f"Failed to parse message {uid}: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise
    
    def _parse_message(self, uid: int, data: Dict) -> Optional[EmailMessage]:
        """Parse raw email data into EmailMessage"""
        try:
            raw_email = data[b'RFC822']
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            message_id = msg.get('Message-ID', f'<uid-{uid}>')
            subject = self._decode_header(msg.get('Subject', ''))
            sender = self._extract_email_address(msg.get('From', ''))
            to_address = self._extract_email_address(msg.get('To', ''))
            date_str = msg.get('Date')
            received_at = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()
            
            # Extract body
            body, html_body = self._extract_body(msg)
            
            return EmailMessage(
                message_id=message_id,
                uid=uid,
                subject=subject,
                sender=sender,
                to_address=to_address,
                body=body,
                html_body=html_body,
                received_at=received_at
            )
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header (handles encoding)"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        result = []
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(str(part))
        
        return ''.join(result)
    
    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from 'From' header"""
        if not from_header:
            return ""
        
        # Parse using email.utils
        parsed = email.utils.parseaddr(from_header)
        return parsed[1] if parsed else from_header
    
    def _extract_body(self, msg: email.message.Message) -> Tuple[str, Optional[str]]:
        """
        Extract email body (text and HTML).
        
        Returns:
            Tuple of (plain_text_body, html_body)
        """
        text_body = None
        html_body = None
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    
                    charset = part.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='replace')
                    
                    if content_type == 'text/plain' and not text_body:
                        text_body = decoded
                    elif content_type == 'text/html' and not html_body:
                        html_body = decoded
                        
                except Exception as e:
                    logger.warning(f"Failed to decode part: {e}")
                    continue
        else:
            # Single part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='replace')
                    
                    if msg.get_content_type() == 'text/html':
                        html_body = decoded
                    else:
                        text_body = decoded
            except Exception as e:
                logger.warning(f"Failed to decode message: {e}")
        
        # If we have HTML but no text, convert HTML to text
        if html_body and not text_body:
            text_body = self._html_to_text(html_body)
        
        return text_body or "", html_body
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            logger.warning(f"Failed to convert HTML to text: {e}")
            return html
    
    def mark_as_read(self, uids: List[int]) -> None:
        """Mark messages as read"""
        if not self.client or not uids:
            return
        
        try:
            self.client.add_flags(uids, [b'\\Seen'])
            logger.info(f"Marked {len(uids)} message(s) as read")
        except Exception as e:
            logger.error(f"Failed to mark messages as read: {e}")
    
    def move_to_folder(self, uids: List[int], folder: str) -> None:
        """Move messages to another folder"""
        if not self.client or not uids:
            return
        
        try:
            self.client.copy(uids, folder)
            self.client.delete_messages(uids)
            self.client.expunge()
            logger.info(f"Moved {len(uids)} message(s) to {folder}")
        except Exception as e:
            logger.error(f"Failed to move messages to {folder}: {e}")
