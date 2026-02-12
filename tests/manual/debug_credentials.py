#!/usr/bin/env python3
"""Debug: Show exact credentials being loaded"""
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")

print(f"Username: '{username}'")
print(f"Password length: {len(password)}")
print(f"Password (shown): '{password}'")
print(f"Has spaces: {' ' in password}")
print(f"Has newlines: {'\\n' in password}")
print(f"Stripped password: '{password.strip()}'")
print(f"Stripped length: {len(password.strip())}")
