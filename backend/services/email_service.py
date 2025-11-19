import smtplib
import threading
from email.mime.text import MIMEText
from app.config.settings import settings
from app.config.logging import logger

def send_email(subject: str, body: str, recipients: list[str]) -> bool:
    """
    Sends an email to a list of recipients using the configured SMTP server.
    Returns True if successful, False otherwise.
    """
    if not recipients:
        logger.warning("📧 No recipients provided for email alert.")
        return False
        
    if not settings.sender_email or not settings.sender_password:
        logger.error("❌ Email configuration missing (SENDER_EMAIL or SENDER_PASSWORD).")
        return False

    try:
        # 1. Setup the message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = settings.sender_email
        msg['To'] = ", ".join(recipients)

        # 2. Connect to Gmail
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(settings.sender_email, settings.sender_password)
            server.sendmail(settings.sender_email, recipients, msg.as_string())
            
        logger.info(f"✅ Email sent to {len(recipients)} recipients: {subject}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {str(e)}")
        return False
    
def send_email_background(subject: str, body: str, recipients: list[str]):
    """
    Runs the email sending in a separate thread so the API will NOT block.
    """
    thread = threading.Thread(
        target=send_email,
        args=(subject, body, recipients),
        daemon=True  # dies automatically if process exits
    )
    thread.start()