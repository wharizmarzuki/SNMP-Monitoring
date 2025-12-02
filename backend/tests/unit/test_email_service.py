"""
Unit tests for Email Service

Tests email sending functionality with mocked SMTP server.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.email_service import send_email, send_email_background


@pytest.mark.unit
class TestEmailService:
    """Test email sending functionality"""

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_success(self, mock_settings, mock_smtp):
        """Test: Email is sent successfully via SMTP"""
        # Setup mock settings
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        # Setup mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        result = send_email(
            subject="Test Alert",
            body="Device 192.168.1.1 CPU > 80%",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("alert@example.com", "password123")
        mock_server.sendmail.assert_called_once()

    @patch('services.email_service.settings')
    def test_send_email_no_recipients(self, mock_settings):
        """Test: Email sending handles empty recipient list"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"

        # Execute
        result = send_email(
            subject="Test Alert",
            body="Test body",
            recipients=[]
        )

        # Assert
        assert result is False

    @patch('services.email_service.settings')
    def test_send_email_missing_configuration(self, mock_settings):
        """Test: Email sending fails when configuration missing"""
        # Setup - missing sender_email
        mock_settings.sender_email = None
        mock_settings.sender_password = "password123"

        # Execute
        result = send_email(
            subject="Test Alert",
            body="Test body",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_smtp_connection_failure(self, mock_settings, mock_smtp):
        """Test: Email sending handles SMTP connection failure"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        # Mock SMTP connection failure
        mock_smtp.side_effect = ConnectionRefusedError("Connection refused")

        # Execute
        result = send_email(
            subject="Test Alert",
            body="Test body",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_authentication_failure(self, mock_settings, mock_smtp):
        """Test: Email sending handles SMTP authentication failure"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "wrong_password"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        # Mock SMTP auth failure
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        result = send_email(
            subject="Test Alert",
            body="Test body",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is False

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_multiple_recipients(self, mock_settings, mock_smtp):
        """Test: Email is sent to multiple recipients"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        recipients = ["admin1@example.com", "admin2@example.com", "admin3@example.com"]
        result = send_email(
            subject="Critical Alert",
            body="Multiple devices down",
            recipients=recipients
        )

        # Assert
        assert result is True
        # Verify sendmail called with all recipients
        call_args = mock_server.sendmail.call_args
        assert call_args[0][1] == recipients

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_correct_headers(self, mock_settings, mock_smtp):
        """Test: Email has correct headers (From, To, Subject)"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        result = send_email(
            subject="Test Subject",
            body="Test Body",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is True
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Subject: Test Subject" in email_content
        assert "From: alert@example.com" in email_content
        assert "To: admin@example.com" in email_content

    @patch('services.email_service.threading.Thread')
    @patch('services.email_service.send_email')
    def test_send_email_background(self, mock_send_email, mock_thread):
        """Test: Background email sending starts thread"""
        # Setup
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Execute
        send_email_background(
            subject="Background Alert",
            body="Test",
            recipients=["admin@example.com"]
        )

        # Assert
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Verify thread is daemon
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs['daemon'] is True

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_body_content(self, mock_settings, mock_smtp):
        """Test: Email body content is correctly formatted"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        test_body = """
        Alert: CPU Usage High
        Device: 192.168.1.1
        Value: 95%
        Threshold: 80%
        """
        result = send_email(
            subject="CPU Alert",
            body=test_body,
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is True
        call_args = mock_server.sendmail.call_args
        email_content = call_args[0][2]
        assert "Alert: CPU Usage High" in email_content
        assert "Device: 192.168.1.1" in email_content


@pytest.mark.unit
class TestEmailServiceEdgeCases:
    """Test edge cases and error handling"""

    @patch('services.email_service.smtplib.SMTP')
    @patch('services.email_service.settings')
    def test_send_email_with_special_characters_in_subject(self, mock_settings, mock_smtp):
        """Test: Email handles special characters in subject"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"
        mock_settings.smtp_server = "smtp.gmail.com"
        mock_settings.smtp_port = 587

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Execute
        result = send_email(
            subject="Alert: Device 192.168.1.1 [CRITICAL] <Down>",
            body="Test",
            recipients=["admin@example.com"]
        )

        # Assert
        assert result is True

    @patch('services.email_service.settings')
    def test_send_email_none_recipients(self, mock_settings):
        """Test: Email sending handles None recipients"""
        # Setup
        mock_settings.sender_email = "alert@example.com"
        mock_settings.sender_password = "password123"

        # Execute
        result = send_email(
            subject="Test",
            body="Test",
            recipients=None
        )

        # Assert
        assert result is False
