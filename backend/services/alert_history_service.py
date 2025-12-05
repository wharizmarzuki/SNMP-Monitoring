"""
Alert history service - Manages alert lifecycle and history tracking.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core import models
from app.config.logging import logger
from typing import Optional


class AlertHistoryService:
    """Service for managing alert history records."""

    @staticmethod
    def create_alert_record(
        db: Session,
        alert_type: str,
        severity: str,
        device_id: int,
        interface_id: Optional[int],
        metric_value: str,
        threshold_value: str,
        message: Optional[str] = None
    ) -> models.AlertHistory:
        """
        Create a new alert history record when alert triggers.

        Args:
            db: Database session
            alert_type: Type of alert (cpu, memory, reachability, interface_status, packet_drop)
            severity: Alert severity (Warning, High, Critical)
            device_id: Device ID
            interface_id: Interface ID (None for device-level alerts)
            metric_value: Current metric value as string
            threshold_value: Threshold value as string
            message: Optional alert message

        Returns:
            Created AlertHistory record
        """
        alert_record = models.AlertHistory(
            alert_type=alert_type,
            severity=severity,
            device_id=device_id,
            interface_id=interface_id,
            triggered_at=datetime.now(timezone.utc),
            metric_value=metric_value,
            threshold_value=threshold_value,
            message=message,
            email_sent=False,
            email_status="pending"
        )
        db.add(alert_record)
        db.flush()  # Get ID without committing
        logger.info(f"📝 Created alert history record: {alert_type} for device_id={device_id}")
        return alert_record

    @staticmethod
    def update_email_status(
        db: Session,
        alert_record: models.AlertHistory,
        success: bool,
        recipients: list[str],
        error: Optional[str] = None
    ):
        """
        Update email sending status for an alert record.

        Args:
            db: Database session
            alert_record: AlertHistory record to update
            success: Whether email was sent successfully
            recipients: List of recipient email addresses
            error: Error message if sending failed
        """
        alert_record.email_sent = True
        alert_record.email_status = "success" if success else "failed"
        alert_record.email_sent_at = datetime.now(timezone.utc)
        alert_record.email_recipients = ", ".join(recipients)
        if error:
            alert_record.email_error = error[:500]  # Truncate to fit column
        db.add(alert_record)
        logger.info(f"✉️ Updated email status for alert {alert_record.id}: {alert_record.email_status}")

    @staticmethod
    def record_user_action(
        db: Session,
        alert_record: models.AlertHistory,
        action: str,
        user_id: Optional[int],
        notes: Optional[str] = None
    ):
        """
        Record user action on an alert (acknowledge or resolve).
        Overwrites previous action (only last action is kept).

        Args:
            db: Database session
            alert_record: AlertHistory record to update
            action: Action taken ("acknowledged" or "resolved")
            user_id: ID of user who performed action
            notes: Optional user notes/reason
        """
        alert_record.action_taken = action
        alert_record.action_at = datetime.now(timezone.utc)
        alert_record.action_by = user_id
        alert_record.action_notes = notes

        # If resolving manually, mark as cleared
        if action == "resolved":
            alert_record.cleared_at = datetime.now(timezone.utc)

        db.add(alert_record)
        logger.info(f"👤 User action recorded: {action} on alert {alert_record.id} by user {user_id}")

    @staticmethod
    def record_auto_clear(
        db: Session,
        alert_record: models.AlertHistory,
        message: Optional[str] = None
    ):
        """
        Record automatic alert clearance (metric returned to normal).

        Args:
            db: Database session
            alert_record: AlertHistory record to update
            message: Optional recovery message
        """
        alert_record.cleared_at = datetime.now(timezone.utc)
        alert_record.action_taken = "auto_cleared"
        alert_record.action_at = datetime.now(timezone.utc)
        alert_record.action_by = None  # System action
        if message:
            alert_record.action_notes = message
        db.add(alert_record)
        logger.info(f"✅ Auto-cleared alert {alert_record.id}")

    @staticmethod
    def get_active_alert_record(
        db: Session,
        alert_type: str,
        device_id: int,
        interface_id: Optional[int] = None
    ) -> Optional[models.AlertHistory]:
        """
        Get the active (uncleaned) alert history record for a specific alert.

        Args:
            db: Database session
            alert_type: Type of alert
            device_id: Device ID
            interface_id: Interface ID (for interface alerts)

        Returns:
            Active AlertHistory record or None
        """
        query = db.query(models.AlertHistory).filter(
            models.AlertHistory.alert_type == alert_type,
            models.AlertHistory.device_id == device_id,
            models.AlertHistory.cleared_at.is_(None)
        )

        if interface_id is not None:
            query = query.filter(models.AlertHistory.interface_id == interface_id)
        else:
            query = query.filter(models.AlertHistory.interface_id.is_(None))

        return query.first()
