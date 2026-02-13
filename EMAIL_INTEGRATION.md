# Email Integration Setup Guide

## Overview

The email integration allows the system to:
1. Poll Gmail inbox for new emails
2. Extract and clean email content
3. Process through existing workflow API
4. Send responses back via email

## Prerequisites

### 1. Gmail Account Setup

You need a Gmail account with **App Password** enabled (not your regular password).

#### Steps to Get Gmail App Password:

1. **Enable 2-Factor Authentication**
   - Go to: https://myaccount.google.com/security
   - Under "Signing in to Google", enable "2-Step Verification"

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → Enter "Omni Channel AI"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Update .env File**
   ```bash
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop  # The app password (remove spaces)
   ```

### 2. Configuration

Edit `/home/bhargav/interview-Pocs/omni-channel-ai-servicing/.env`:

```env
# Email Configuration
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_POLL_INTERVAL=30  # Check every 30 seconds
SUPPORT_EMAIL=support@yourbank.com
API_BASE_URL=http://localhost:8000
```

## How It Works

### Architecture

```
Gmail Inbox
    ↓
Email Poller (polls every 30s)
    ↓
Email Client (IMAP connection)
    ↓
Email Processor (clean & extract)
    ↓
API Endpoint (/api/v1/service-request)
    ↓
Master Router → Workflow
    ↓
Response → Email Reply (TODO)
```

### Email Flow

1. **Poll Inbox**: Check for UNSEEN emails every 30 seconds
2. **Filter**: Skip auto-replies, system messages
3. **Clean**: Remove signatures, reply chains, HTML
4. **Extract**: Get sender, subject, clean body text
5. **Lookup Customer**: Map email → customer_id (via CRM)
6. **Build Payload**:
   ```json
   {
     "user_message": "I want to update my address...",
     "customer_id": "EMAIL-john@example.com",
     "channel": "email",
     "metadata": {
       "email_sender": "john@example.com",
       "email_subject": "Address Update",
       "email_message_id": "<msg-123@gmail.com>"
     }
   }
   ```
7. **POST to API**: Send to `/api/v1/service-request`
8. **Mark as Read**: Mark email as processed
9. **Send Response**: Reply via email (TODO: needs SMTP)

## Two Approaches: Polling vs IMAP IDLE

### Approach Comparison

| Feature | Polling (email_poller.py) | IMAP IDLE (email_idle_poller.py) |
|---------|---------------------------|-----------------------------------|
| **Response Time** | 30 second delay | Instant notification |
| **Resource Usage** | Checks every 30s | Only wakes on new mail |
| **Connection** | May go stale | Built-in keepalive |
| **Gmail Support** | ✅ | ✅ |
| **Simplicity** | Simple loop | Slightly more complex |
| **Best For** | Testing, simple setups | Production, real-time |

**Recommendation**: Use **IMAP IDLE** (`email_idle_poller.py`) for production - it's more efficient and responsive.

## Running the Email Service

### Option 1: IMAP IDLE (Recommended - Push Notifications)

```bash
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing

# Make sure API server is running
python3 -m uvicorn omni_channel_ai_servicing.app.main:app --port 8000 &

# Start email IDLE service (instant notifications)
PYTHONPATH=/home/bhargav/interview-Pocs/omni-channel-ai-servicing python3 -m omni_channel_ai_servicing.services.email_idle_poller
```

### Option 2: Polling (Simple - 30s Intervals)

```bash
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing

# Make sure API server is running
python3 -m uvicorn omni_channel_ai_servicing.app.main:app --port 8000 &

# Start email poller (checks every 30s)
PYTHONPATH=/home/bhargav/interview-Pocs/omni-channel-ai-servicing python3 -m omni_channel_ai_servicing.services.email_poller
```

### Option 3: Background Service (Production)

**For IMAP IDLE (recommended):**
```bash
# Start in background with nohup
nohup python3 -m omni_channel_ai_servicing.services.email_idle_poller > /tmp/email_idle.log 2>&1 &

# Check logs
tail -f /tmp/email_idle.log

# Stop
pkill -f email_idle_poller.py
```

**For Polling:**
```bash
# Start in background with nohup
nohup python3 -m omni_channel_ai_servicing.services.email_poller > /tmp/email_poller.log 2>&1 &

# Check logs
tail -f /tmp/email_poller.log

# Stop
pkill -f email_poller.py
```

## Testing

### 1. Test Email Processing (No Connection)

```bash
python3 test_email_simple.py
```

This tests email cleaning without connecting to Gmail.

### 2. Test with Real Gmail (After Setup)

**Using IMAP IDLE (recommended):**
1. **Start API server**:
   ```bash
   python3 -m uvicorn omni_channel_ai_servicing.app.main:app --port 8000
   ```

2. **Start email IDLE service**:
   ```bash
   PYTHONPATH=$(pwd) python3 -m omni_channel_ai_servicing.services.email_idle_poller
   ```

3. **Send test email** to your Gmail address:
   - Subject: "Test: Address Update"
   - Body: "Please update my address to 123 Oak St, Austin TX 78701"

4. **Watch logs**: You should see **instant notification**:
   ```
   🔔 Starting IDLE mode - waiting for new emails...
   📬 New email notification received!
   📧 Processing 1 new email(s)
   Processing email from you@gmail.com: Test: Address Update
   Sending to API: customer_id=EMAIL-you@gmail.com
   ✅ Email processed successfully
   ```

**Using Polling (alternative):**
1. **Start API server**:
   ```bash
   python3 -m uvicorn omni_channel_ai_servicing.app.main:app --port 8000
   ```

2. **Start email poller**:
   ```bash
   PYTHONPATH=$(pwd) python3 -m omni_channel_ai_servicing.services.email_poller
   ```

3. **Send test email** to your Gmail address

4. **Watch logs** (may take up to 30 seconds):
   ```
   📧 Processing 1 new email(s)
   Processing email from you@gmail.com: Test: Address Update
   Sending to API: customer_id=EMAIL-you@gmail.com
   ✅ Email processed successfully
   ```

## Example Test Emails

### Address Update
```
Subject: Need to update my address
Body:
Hi Support,

Please update my address to:
456 Pine Street
Dallas, TX 75201

Thanks!
```

### Transaction Dispute
```
Subject: Dispute charge
Body:
Hello,

I want to dispute a charge of $250 from MegaMart on transaction TXN-12345.
I didn't authorize this purchase.

Please help.
```

### Statement Request
```
Subject: Need statement
Body:
Hi,

I need my January 2026 account statement.

Thanks
```

## Monitoring

### Logs

The poller logs all activity:
- Connection status
- Emails found
- Processing results
- API responses
- Errors

### Metrics to Watch

- **Emails processed**: Should increment when new emails arrive
- **API success rate**: Check for failed API calls
- **Processing time**: Should be < 5 seconds per email
- **Error rate**: Should be near zero

## Troubleshooting

### "Failed to connect to email server"
- Check Gmail app password is correct
- Verify 2FA is enabled
- Check firewall allows port 993

### "No module named 'imapclient'"
```bash
pip install imapclient email-reply-parser beautifulsoup4 --break-system-packages
```

### "API request failed: 404"
- Make sure API server is running on port 8000
- Check API_BASE_URL in .env

### Emails not being processed
- Check email filter (might be auto-reply)
- Verify email is UNSEEN
- Check poller logs for errors

## Next Steps

### TODO:
1. **SMTP Email Responses**: Implement actual email sending (currently just logs)
2. **CRM Integration**: Real customer lookup instead of EMAIL- prefix
3. **Email Templates**: Professional response templates
4. **Attachment Handling**: Process PDFs, images
5. **Email Threading**: Proper In-Reply-To headers
6. **Rate Limiting**: Respect Gmail API limits
7. **Monitoring**: Prometheus metrics, alerts

## Security Notes

- **Never commit .env to git** (contains passwords)
- Use app passwords, not main Gmail password
- Consider using OAuth2 for production
- Implement rate limiting
- Sanitize all email content before processing
