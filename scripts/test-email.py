#!/usr/bin/env python3
"""
SNMP Monitoring System - Email Configuration Tester
====================================================
This script tests your email configuration by sending a test alert email.
It uses the same email settings from your .env file that the monitoring system uses.

Usage:
    python scripts/test-email.py
    or
    make test-email
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text):
    """Print a colored header"""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")


def print_success(text):
    """Print a success message"""
    print(f"{GREEN}✓{NC} {text}")


def print_error(text):
    """Print an error message"""
    print(f"{RED}✗{NC} {text}")


def print_warning(text):
    """Print a warning message"""
    print(f"{YELLOW}⚠{NC} {text}")


def print_info(text):
    """Print an info message"""
    print(f"  {text}")


def load_email_config():
    """Load email configuration from .env file"""
    env_file = backend_dir / ".env"

    if not env_file.exists():
        print_error("Backend .env file not found!")
        print_info("Run ./setup.sh to create configuration")
        sys.exit(1)

    # Load environment variables
    load_dotenv(env_file)

    config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_password': os.getenv('SENDER_PASSWORD', ''),
    }

    # Validate configuration
    if not config['sender_email']:
        print_error("SENDER_EMAIL is not configured in .env")
        sys.exit(1)

    if not config['sender_password']:
        print_error("SENDER_PASSWORD is not configured in .env")
        sys.exit(1)

    return config


def create_test_email(sender_email, recipient_email):
    """Create a test email message"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'SNMP Monitoring - Test Email'
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Create text version
    text = f"""
SNMP Monitoring System - Test Email
====================================

This is a test email to verify your email configuration.

If you're reading this, your email settings are working correctly!

Test Details:
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: {sender_email}
- To: {recipient_email}

You can now expect to receive alert notifications from your SNMP monitoring system.

---
SNMP Monitoring System
    """

    # Create HTML version
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
          <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
            SNMP Monitoring System - Test Email
          </h2>

          <p style="font-size: 16px;">
            This is a test email to verify your email configuration.
          </p>

          <div style="background-color: #10b981; color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong>✓ Success!</strong> If you're reading this, your email settings are working correctly!
          </div>

          <h3 style="color: #374151; margin-top: 20px;">Test Details:</h3>
          <ul style="background-color: #f9fafb; padding: 15px; border-left: 3px solid #2563eb;">
            <li><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li><strong>From:</strong> {sender_email}</li>
            <li><strong>To:</strong> {recipient_email}</li>
          </ul>

          <p style="margin-top: 20px;">
            You can now expect to receive alert notifications from your SNMP monitoring system.
          </p>

          <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

          <p style="font-size: 12px; color: #6b7280;">
            SNMP Monitoring System<br>
            This is an automated test message
          </p>
        </div>
      </body>
    </html>
    """

    # Attach both versions
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    return msg


def send_test_email(config, recipient_email):
    """Send a test email using the provided configuration"""
    try:
        print_info("Creating connection to SMTP server...")

        # Create SMTP connection
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.set_debuglevel(0)  # Set to 1 for verbose output

        print_info("Starting TLS encryption...")
        server.starttls()

        print_info("Logging in...")
        server.login(config['sender_email'], config['sender_password'])

        print_info("Composing test email...")
        msg = create_test_email(config['sender_email'], recipient_email)

        print_info("Sending email...")
        server.send_message(msg)

        print_info("Closing connection...")
        server.quit()

        return True, None

    except smtplib.SMTPAuthenticationError as e:
        return False, f"Authentication failed: {str(e)}\n\nFor Gmail, make sure you're using an App Password:\nhttps://myaccount.google.com/apppasswords"

    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    """Main function"""
    print_header("SNMP Monitoring - Email Configuration Tester")

    # Load configuration
    print_info("Loading email configuration from .env...")
    try:
        config = load_email_config()
        print_success("Configuration loaded successfully")
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Display configuration
    print("\nCurrent Configuration:")
    print(f"  SMTP Server: {config['smtp_server']}")
    print(f"  SMTP Port: {config['smtp_port']}")
    print(f"  Sender Email: {config['sender_email']}")
    print(f"  Password: {'*' * len(config['sender_password'])} (hidden)")

    # Ask for recipient
    print("\n")
    recipient = input(f"Enter recipient email address [{config['sender_email']}]: ").strip()

    if not recipient:
        recipient = config['sender_email']

    # Validate recipient email
    if '@' not in recipient:
        print_error("Invalid email address")
        sys.exit(1)

    print("\n")
    confirm = input(f"Send test email to {recipient}? [Y/n]: ").strip().lower()

    if confirm and confirm not in ['y', 'yes']:
        print("Cancelled")
        sys.exit(0)

    # Send test email
    print_header("Sending Test Email")

    success, error = send_test_email(config, recipient)

    print("\n")
    if success:
        print_success("Test email sent successfully!")
        print("\n")
        print("Next steps:")
        print(f"  1. Check your inbox at {recipient}")
        print("  2. Look for an email from:", config['sender_email'])
        print("  3. Check your spam folder if you don't see it")
        print("\n")
        print("If you received the email, your configuration is working correctly!")
        sys.exit(0)
    else:
        print_error("Failed to send test email")
        print("\n")
        print_warning("Error details:")
        print(f"  {error}")
        print("\n")
        print("Common solutions:")
        print("  1. For Gmail: Use an App Password, not your regular password")
        print("     https://myaccount.google.com/apppasswords")
        print("  2. Verify SMTP_SERVER and SMTP_PORT in .env are correct")
        print("  3. Check your email credentials")
        print("  4. Ensure 'Less secure app access' is enabled (if applicable)")
        print("\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
