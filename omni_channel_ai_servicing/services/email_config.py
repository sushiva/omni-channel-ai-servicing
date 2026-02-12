"""
Email service configuration.

To use Gmail:
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to .env file:
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class EmailConfig:
    """Email service configuration"""
    
    # IMAP Server Settings (for reading emails)
    IMAP_HOST: str = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
    IMAP_PORT: int = int(os.getenv("EMAIL_IMAP_PORT", "993"))
    
    # SMTP Server Settings (for sending emails)
    SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))  # TLS port
    
    # Email Credentials (same for IMAP and SMTP)
    USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Customer Support")
    
    # Polling Settings
    POLL_INTERVAL: int = int(os.getenv("EMAIL_POLL_INTERVAL", "30"))  # seconds
    MAILBOX: str = os.getenv("EMAIL_MAILBOX", "INBOX")
    
    # Processing Settings
    MARK_AS_READ: bool = os.getenv("EMAIL_MARK_AS_READ", "true").lower() == "true"
    PROCESS_FOLDER: Optional[str] = os.getenv("EMAIL_PROCESS_FOLDER", "Processed")
    SKIP_EXISTING_ON_STARTUP: bool = os.getenv("EMAIL_SKIP_EXISTING", "true").lower() == "true"
    
    # Support Email (emails TO this address will be processed)
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@bank.com")
    
    # API Settings
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8001")
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if email is properly configured"""
        return bool(cls.USERNAME and cls.PASSWORD)
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration and raise error if invalid"""
        if not cls.USERNAME:
            raise ValueError("EMAIL_USERNAME not configured in .env")
        if not cls.PASSWORD:
            raise ValueError("EMAIL_PASSWORD not configured in .env")
        if "@" not in cls.USERNAME:
            raise ValueError("EMAIL_USERNAME must be a valid email address")
