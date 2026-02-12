#!/usr/bin/env python3
"""Quick test to verify Gmail credentials"""
import os
from dotenv import load_dotenv
from imapclient import IMAPClient

load_dotenv()

username = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")

print(f"Testing connection to Gmail...")
print(f"Username: {username}")
print(f"Password: {'*' * len(password)} ({len(password)} chars)")

try:
    client = IMAPClient("imap.gmail.com", port=993, use_uid=True, ssl=True)
    print("✅ Connected to IMAP server")
    
    client.login(username, password)
    print("✅ Login successful!")
    
    client.select_folder("INBOX")
    print("✅ Selected INBOX")
    
    client.logout()
    print("\n🎉 Gmail credentials are working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Enable 2FA: https://myaccount.google.com/security")
    print("2. Generate App Password: https://myaccount.google.com/apppasswords")
    print("3. Copy password WITHOUT spaces")
    print("4. Update EMAIL_PASSWORD in .env")
