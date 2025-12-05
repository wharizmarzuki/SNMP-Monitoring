"""
Email notification service for alert delivery.
Sends emails via SMTP with non-blocking background execution and status callbacks.
"""
import smtplib
import threading
from email.mime.text import MIMEText
from typing import Callable, Optional
from app.config.settings import settings
from app.config.logging import logger


def send_email(subject: str, body: str, recipients: list[str]) -> tuple[bool, Optional[str]]:
    """
    Send email to recipients using configured SMTP server.

    Returns:
        Tuple of (success: bool, error_message: str | None)
    """
    if not recipients:
        logger.warning("📧 No recipients provided for email alert.")
        return False, "No recipients provided"

    if not settings.sender_email or not settings.sender_password:
        logger.error("❌ Email configuration missing (SENDER_EMAIL or SENDER_PASSWORD).")
        return False, "Email configuration missing"

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = settings.sender_email
        msg['To'] = ", ".join(recipients)

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.sender_email, settings.sender_password)
            server.sendmail(settings.sender_email, recipients, msg.as_string())

        logger.info(f"✅ Email sent to {len(recipients)} recipients: {subject}")
        return True, None

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to send email: {error_msg}")
        return False, error_msg


def send_email_background(
    subject: str,
    body: str,
    recipients: list[str],
    callback: Optional[Callable[[bool, list[str], Optional[str]], None]] = None
):
    """
    Execute email sending in separate thread to avoid blocking.

    Args:
        subject: Email subject
        body: Email body
        recipients: List of recipient emails
        callback: Optional callback function called with (success, recipients, error)
    """
    def _send_and_callback():
        success, error = send_email(subject, body, recipients)
        if callback:
            try:
                callback(success, recipients, error)
            except Exception as e:
                logger.error(f"❌ Exception in email callback: {e}", exc_info=True)

    thread = threading.Thread(
        target=_send_and_callback,
        daemon=True
    )
    thread.start()