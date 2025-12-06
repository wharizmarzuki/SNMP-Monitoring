"""
Alert evaluation and notification service with state-based management.
Handles CPU, memory, reachability, and interface alerts with email notifications.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core import models
from app.config.logging import logger
from services.email_service import send_email_background
from services.alert_history_service import AlertHistoryService
from typing import Optional


class AlertEvaluator:

    @staticmethod
    def _notify(subject: str, body: str, db: Session, alert_records: Optional[list[models.AlertHistory]] = None):
        """
        Fetch recipients from database and send email notification.
        Updates alert_records with email status if provided.

        Args:
            subject: Email subject
            body: Email body
            db: Database session
            alert_records: List of alert records to update (or single record in a list), or None
        """
        recipients_db = db.query(models.AlertRecipient).all()
        recipient_list = [r.email for r in recipients_db]

        if not recipient_list:
            logger.warning(f"⚠️ Alert triggered but no recipients found in DB!")
            if alert_records:
                for alert_record in alert_records:
                    AlertHistoryService.update_email_status(db, alert_record, False, [], "No recipients configured")
                db.commit()
            return

        # Extract IDs while the session is still active to avoid DetachedInstanceError
        alert_ids = [record.id for record in alert_records] if alert_records else []

        def email_callback(success: bool, recipients: list[str], error: str | None):
            """Callback to update alert history with email status."""
            if alert_ids:
                logger.info(f"📧 Email callback triggered for alert_ids={alert_ids}, success={success}")
                # Need new session for thread-safe database access
                from app.core.database import SessionLocal
                db_thread = SessionLocal()
                try:
                    # Update all alert records in this batch
                    for alert_id in alert_ids:
                        record = db_thread.query(models.AlertHistory).filter(
                            models.AlertHistory.id == alert_id
                        ).first()
                        if record:
                            AlertHistoryService.update_email_status(db_thread, record, success, recipients, error)
                            logger.info(f"✉️ Successfully updated email status for alert {alert_id}")
                        else:
                            logger.warning(f"⚠️ Could not find alert record {alert_id} to update email status")
                    db_thread.commit()
                except Exception as e:
                    logger.error(f"❌ Failed to update email status for alerts {alert_ids}: {e}")
                    db_thread.rollback()
                finally:
                    db_thread.close()

        send_email_background(subject, body, recipient_list, callback=email_callback)

    @staticmethod
    def evaluate_cpu(device: models.Device, current_val: float, db: Session):
        """
        Evaluate CPU threshold and manage alert state.
        Supports maintenance mode and acknowledgment.
        """
        if device.maintenance_mode and device.maintenance_until:
            if datetime.now(timezone.utc) < device.maintenance_until:
                return False  # Suppress all alerts during maintenance
            else:
                # Maintenance window expired, disable it
                device.maintenance_mode = False
                device.maintenance_until = None
                device.maintenance_reason = None

        is_triggered = False

        if current_val > device.cpu_threshold:
            if device.cpu_alert_state == "clear":
                logger.warning(f"⚠️ ALERT: {device.hostname} High CPU: {current_val}%")

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                exceeded_by = round(current_val - device.cpu_threshold, 2)

                # Determine severity
                severity = "Critical" if current_val >= 90 else "High" if current_val >= 75 else "Warning"

                # Create alert history record
                alert_record = AlertHistoryService.create_alert_record(
                    db=db,
                    alert_type="cpu",
                    severity=severity,
                    device_id=device.id,
                    interface_id=None,
                    metric_value=f"{current_val}%",
                    threshold_value=f">{device.cpu_threshold}%",
                    message=f"CPU utilization exceeded threshold by {exceeded_by}%"
                )

                subject = f"[CRITICAL] CPU Usage Alert - {device.hostname}"
                body = f"""Dear Network Administrator,

This is an automated alert from your SNMP Network Monitoring System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ALERT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          CPU Threshold Exceeded
Severity:            CRITICAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

METRICS:
  Current CPU Usage:     {current_val}%
  Configured Threshold:  {device.cpu_threshold}%
  Exceeded By:          {exceeded_by}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Check running processes on the device
2. Verify if any scheduled tasks or backups are running
3. Review system logs for unusual activity
4. Consider scaling resources if this is a recurring issue
5. Acknowledge this alert in the monitoring dashboard once addressed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db, [alert_record])

                device.cpu_alert_state = "triggered"
                device.cpu_alert_sent = True
                is_triggered = True
            elif device.cpu_alert_state == "triggered":
                pass
            elif device.cpu_alert_state == "acknowledged":
                pass
        else:
            if device.cpu_alert_state in ["triggered", "acknowledged"]:
                logger.info(f"✅ RECOVERY: {device.hostname} CPU Normal")

                # Find and close alert history record
                alert_record = AlertHistoryService.get_active_alert_record(
                    db=db,
                    alert_type="cpu",
                    device_id=device.id
                )
                if alert_record:
                    AlertHistoryService.record_auto_clear(
                        db=db,
                        alert_record=alert_record,
                        message=f"CPU returned to normal: {current_val}%"
                    )

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                subject = f"[RESOLVED] CPU Usage Normal - {device.hostname}"
                body = f"""Dear Network Administrator,

Good news! Your SNMP Network Monitoring System has detected a recovery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOVERY DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          CPU Usage Recovered
Severity:            INFORMATIONAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

METRICS:
  Current CPU Usage:     {current_val}%
  Configured Threshold:  {device.cpu_threshold}%
  Status:               NORMAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The CPU usage has returned to normal levels. No further action is required.
The alert has been automatically cleared in the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db)

                device.cpu_alert_state = "clear"
                device.cpu_acknowledged_at = None
                device.cpu_alert_sent = False
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_memory(device: models.Device, current_val: float, db: Session):
        """
        Evaluate memory threshold and manage alert state.
        Supports maintenance mode and acknowledgment.
        """
        if device.maintenance_mode and device.maintenance_until:
            if datetime.now(timezone.utc) < device.maintenance_until:
                return False

        is_triggered = False

        if current_val > device.memory_threshold:
            if device.memory_alert_state == "clear":
                logger.warning(f"⚠️ ALERT: {device.hostname} High Memory: {current_val}%")

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                exceeded_by = round(current_val - device.memory_threshold, 2)

                # Determine severity
                severity = "Critical" if current_val >= 90 else "High" if current_val >= 75 else "Warning"

                # Create alert history record
                alert_record = AlertHistoryService.create_alert_record(
                    db=db,
                    alert_type="memory",
                    severity=severity,
                    device_id=device.id,
                    interface_id=None,
                    metric_value=f"{current_val}%",
                    threshold_value=f">{device.memory_threshold}%",
                    message=f"Memory utilization exceeded threshold by {exceeded_by}%"
                )

                subject = f"[CRITICAL] Memory Usage Alert - {device.hostname}"
                body = f"""Dear Network Administrator,

This is an automated alert from your SNMP Network Monitoring System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ALERT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Memory Threshold Exceeded
Severity:            CRITICAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

METRICS:
  Current Memory Usage:  {current_val}%
  Configured Threshold:  {device.memory_threshold}%
  Exceeded By:          {exceeded_by}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Identify memory-intensive processes
2. Check for memory leaks in applications
3. Review recent configuration changes
4. Consider clearing cache or restarting services
5. Acknowledge this alert in the monitoring dashboard once addressed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db, [alert_record])

                device.memory_alert_state = "triggered"
                device.memory_alert_sent = True
                is_triggered = True
            elif device.memory_alert_state == "triggered":
                pass
            elif device.memory_alert_state == "acknowledged":
                pass
        else:
            if device.memory_alert_state in ["triggered", "acknowledged"]:
                logger.info(f"✅ RECOVERY: {device.hostname} Memory Normal")

                # Find and close alert history record
                alert_record = AlertHistoryService.get_active_alert_record(
                    db=db,
                    alert_type="memory",
                    device_id=device.id
                )
                if alert_record:
                    AlertHistoryService.record_auto_clear(
                        db=db,
                        alert_record=alert_record,
                        message=f"Memory returned to normal: {current_val}%"
                    )

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                subject = f"[RESOLVED] Memory Usage Normal - {device.hostname}"
                body = f"""Dear Network Administrator,

Good news! Your SNMP Network Monitoring System has detected a recovery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOVERY DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Memory Usage Recovered
Severity:            INFORMATIONAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

METRICS:
  Current Memory Usage:  {current_val}%
  Configured Threshold:  {device.memory_threshold}%
  Status:               NORMAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The memory usage has returned to normal levels. No further action is required.
The alert has been automatically cleared in the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db)

                device.memory_alert_state = "clear"
                device.memory_acknowledged_at = None
                device.memory_alert_sent = False
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_reachability(device: models.Device, db: Session):
        """
        Evaluate device reachability and manage alert state.
        Returns True if alert state changed, False otherwise.
        """
        if device.maintenance_mode and device.maintenance_until:
            if datetime.now(timezone.utc) < device.maintenance_until:
                return False

        is_triggered = False

        if not device.is_reachable:
            if device.reachability_alert_state == "clear":
                logger.error(
                    f"🔴 ALERT: {device.hostname} ({device.ip_address}) is UNREACHABLE "
                    f"after {device.consecutive_failures} consecutive failures"
                )

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                last_success = device.last_poll_success.strftime("%Y-%m-%d %H:%M:%S UTC") if device.last_poll_success else "Never"
                last_attempt = device.last_poll_attempt.strftime("%Y-%m-%d %H:%M:%S UTC") if device.last_poll_attempt else "Unknown"

                # Create alert history record
                alert_record = AlertHistoryService.create_alert_record(
                    db=db,
                    alert_type="reachability",
                    severity="Critical",
                    device_id=device.id,
                    interface_id=None,
                    metric_value=f"Last seen: {last_success}",
                    threshold_value=f">{device.failure_threshold} failures",
                    message=f"Device unreachable after {device.consecutive_failures} consecutive failures"
                )

                subject = f"[CRITICAL] Device Unreachable - {device.hostname}"
                body = f"""Dear Network Administrator,

This is an automated alert from your SNMP Network Monitoring System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ALERT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Device Connectivity Loss
Severity:            CRITICAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

CONNECTIVITY STATUS:
  Status:                    UNREACHABLE
  Consecutive Failures:      {device.consecutive_failures}
  Last Successful Poll:      {last_success}
  Last Poll Attempt:         {last_attempt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMMEDIATE:
1. Verify physical connectivity to the device
2. Check if the device is powered on
3. Ping the device to confirm network connectivity
4. Review firewall rules and SNMP configuration

FOLLOW-UP:
5. Check network switch port status
6. Verify VLAN and routing configuration
7. Review recent network changes
8. If issue persists, schedule on-site investigation
9. Acknowledge this alert in the monitoring dashboard once addressed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db, [alert_record])

                device.reachability_alert_state = "triggered"
                device.reachability_alert_sent = True
                is_triggered = True
            elif device.reachability_alert_state == "triggered":
                pass
            elif device.reachability_alert_state == "acknowledged":
                pass
        else:
            if device.reachability_alert_state in ["triggered", "acknowledged"]:
                logger.info(
                    f"✅ RECOVERY: {device.hostname} ({device.ip_address}) is REACHABLE again"
                )

                # Find and close alert history record
                alert_record = AlertHistoryService.get_active_alert_record(
                    db=db,
                    alert_type="reachability",
                    device_id=device.id
                )
                if alert_record:
                    AlertHistoryService.record_auto_clear(
                        db=db,
                        alert_record=alert_record,
                        message="Device connectivity restored"
                    )

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                last_success = device.last_poll_success.strftime("%Y-%m-%d %H:%M:%S UTC") if device.last_poll_success else "Just now"

                subject = f"[RESOLVED] Device Recovered - {device.hostname}"
                body = f"""Dear Network Administrator,

Good news! Your SNMP Network Monitoring System has detected a recovery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOVERY DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Device Connectivity Restored
Severity:            INFORMATIONAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}

CONNECTIVITY STATUS:
  Status:                   REACHABLE
  Last Successful Poll:     {last_success}
  Consecutive Failures:    0 (Reset)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The device is now responding to SNMP polls again. No further action is required.
The alert has been automatically cleared in the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

                AlertEvaluator._notify(subject, body, db)

                device.reachability_alert_state = "clear"
                device.reachability_acknowledged_at = None
                device.reachability_alert_sent = False
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_interfaces(device: models.Device, db: Session):
        """Check all interfaces for status changes and packet drops."""
        alerts_triggered = []
        alert_records = []
        recoveries_triggered = []

        for interface in device.interfaces:
            # Get the last two metrics to check for state changes
            metrics = db.query(models.InterfaceMetric)\
                .filter(models.InterfaceMetric.interface_id == interface.id)\
                .order_by(models.InterfaceMetric.timestamp.desc())\
                .limit(2)\
                .all()

            if not metrics:
                continue

            latest_metric = metrics[0]
            previous_metric = metrics[1] if len(metrics) > 1 else None

            status_result = AlertEvaluator._check_oper_status(
                device, interface, latest_metric, previous_metric, db
            )
            if status_result:
                msg, alert_record = status_result
                if "DOWN" in msg:
                    alerts_triggered.append(msg)
                    if alert_record:
                        alert_records.append(alert_record)
                else:
                    recoveries_triggered.append(msg)

            drop_result = AlertEvaluator._check_packet_drops(
                device, interface, latest_metric, previous_metric, db
            )
            if drop_result:
                msg, alert_record = drop_result
                if "high discard" in msg:
                    alerts_triggered.append(msg)
                    if alert_record:
                        alert_records.append(alert_record)
                else:
                    recoveries_triggered.append(msg)

        if alerts_triggered:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            alert_count = len(alerts_triggered)

            subject = f"[CRITICAL] Interface Alert(s) - {device.hostname}"
            body = f"""Dear Network Administrator,

This is an automated alert from your SNMP Network Monitoring System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ALERT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Interface Alert(s)
Severity:            CRITICAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}
Alert Count:         {alert_count}

AFFECTED INTERFACE(S):
"""
            for msg in alerts_triggered:
                body += f"  • {msg}\n"

            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Check physical cable connections for affected interfaces
2. Verify switch port configuration and status
3. Review interface error counters and logs
4. Check for network loops or broadcast storms
5. Verify VLAN and trunk configuration
6. Acknowledge alerts in the monitoring dashboard once addressed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

            AlertEvaluator._notify(subject, body, db, alert_records if alert_records else None)

        if recoveries_triggered:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            recovery_count = len(recoveries_triggered)

            subject = f"[RESOLVED] Interface Recovery - {device.hostname}"
            body = f"""Dear Network Administrator,

Good news! Your SNMP Network Monitoring System has detected interface recovery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOVERY DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alert Type:          Interface Recovery
Severity:            INFORMATIONAL
Device Name:         {device.hostname}
IP Address:          {device.ip_address}
Timestamp:           {timestamp}
Recovery Count:      {recovery_count}

RECOVERED INTERFACE(S):
"""
            for msg in recoveries_triggered:
                body += f"  • {msg}\n"

            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The interface(s) have returned to normal operation. No further action is required.
All related alerts have been automatically cleared in the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification. Please do not reply to this email.
To manage alert settings, log in to your SNMP Monitoring Dashboard.

Best regards,
SNMP Network Monitoring System"""

            AlertEvaluator._notify(subject, body, db)

    @staticmethod
    def _check_oper_status(
        device: models.Device,
        interface: models.Interface,
        latest_metric: models.InterfaceMetric,
        previous_metric: models.InterfaceMetric | None,
        db: Session
    ) -> tuple[str, models.AlertHistory | None] | None:
        """
        Check for UP/DOWN state changes and manage alerts.
        Returns tuple of (message, alert_record) if notifiable event occurred, else None.
        """
        is_down = (latest_metric.oper_status != 1)

        if is_down:
            if interface.oper_status_alert_state == "clear":
                if previous_metric is not None:
                    prev_is_down = (previous_metric.oper_status != 1)
                    if not prev_is_down:
                        logger.warning(f"⚠️ ALERT: {device.hostname} Interface {interface.if_name} is DOWN")

                        # Create alert history record
                        alert_record = AlertHistoryService.create_alert_record(
                            db=db,
                            alert_type="interface_status",
                            severity="High",
                            device_id=device.id,
                            interface_id=interface.id,
                            metric_value="Down",
                            threshold_value="Should be Up",
                            message=f"Interface {interface.if_name} changed state to DOWN"
                        )

                        interface.oper_status_alert_state = "triggered"
                        interface.oper_status_alert_sent = True
                        db.add(interface)
                        return (f"Interface {interface.if_name} ({interface.if_index}) is DOWN", alert_record)
            elif interface.oper_status_alert_state == "triggered":
                pass
            elif interface.oper_status_alert_state == "acknowledged":
                pass
        else:
            if interface.oper_status_alert_state in ["triggered", "acknowledged"]:
                logger.info(f"✅ RECOVERY: {device.hostname} Interface {interface.if_name} is UP")

                # Find and close alert history record
                alert_record = AlertHistoryService.get_active_alert_record(
                    db=db,
                    alert_type="interface_status",
                    device_id=device.id,
                    interface_id=interface.id
                )
                if alert_record:
                    AlertHistoryService.record_auto_clear(
                        db=db,
                        alert_record=alert_record,
                        message=f"Interface {interface.if_name} returned to UP state"
                    )

                interface.oper_status_alert_state = "clear"
                interface.oper_status_acknowledged_at = None
                interface.oper_status_alert_sent = False
                db.add(interface)
                return (f"Interface {interface.if_name} ({interface.if_index}) is UP", None)

        return None

    @staticmethod
    def _check_packet_drops(
        device: models.Device,
        interface: models.Interface,
        latest_metric: models.InterfaceMetric,
        previous_metric: models.InterfaceMetric | None,
        db: Session
    ) -> tuple[str, models.AlertHistory | None] | None:
        """
        Check for discard rate threshold breaches and manage alerts.
        Returns tuple of (message, alert_record) if notifiable event occurred, else None.

        Uses delta calculation (current - previous) to calculate true discard rate.
        This matches the logic in query.py for consistency between alerts and dashboards.
        """
        # Require previous metric to calculate delta (rate of change)
        if not previous_metric:
            return None

        # Define safe delta helper (handles counter wraps and resets)
        def get_safe_delta(curr, prev):
            """Calculate delta with counter wrap/reset handling."""
            if curr is None or prev is None:
                return 0

            delta = curr - prev

            # Handle counter wraps/resets
            # Negative delta usually indicates device reboot or counter reset
            # Since we're using 64-bit high-capacity counters, wraps are extremely rare
            if delta < 0:
                return 0  # Discard invalid wrap (consistent with query.py)

            return delta

        # Calculate deltas for discards
        delta_discards_in = get_safe_delta(latest_metric.discards_in, previous_metric.discards_in)
        delta_discards_out = get_safe_delta(latest_metric.discards_out, previous_metric.discards_out)
        total_drop_delta = delta_discards_in + delta_discards_out

        # Calculate deltas for packets (unicast + multicast + broadcast)
        delta_pkts_in = get_safe_delta(latest_metric.packets_in, previous_metric.packets_in)
        delta_pkts_out = get_safe_delta(latest_metric.packets_out, previous_metric.packets_out)

        # Add multicast packets
        delta_mcast_in = get_safe_delta(latest_metric.multicast_packets_in, previous_metric.multicast_packets_in)
        delta_mcast_out = get_safe_delta(latest_metric.multicast_packets_out, previous_metric.multicast_packets_out)

        # Add broadcast packets
        delta_bcast_in = get_safe_delta(latest_metric.broadcast_packets_in, previous_metric.broadcast_packets_in)
        delta_bcast_out = get_safe_delta(latest_metric.broadcast_packets_out, previous_metric.broadcast_packets_out)

        # Total packet delta = unicast + multicast + broadcast
        total_packet_delta = delta_pkts_in + delta_pkts_out + delta_mcast_in + delta_mcast_out + delta_bcast_in + delta_bcast_out

        # Calculate true discard rate percentage
        # Formula: drops / (packets_passed + packets_dropped) * 100
        # Total events = packets that passed + packets that were dropped
        total_events = total_packet_delta + total_drop_delta

        if total_events == 0:
            discard_rate = 0.0
        else:
            discard_rate = (total_drop_delta / total_events) * 100

        is_exceeded = (discard_rate > interface.packet_drop_threshold)

        if is_exceeded:
            if interface.packet_drop_alert_state == "clear":
                # Trigger alert on threshold breach (state transition from clear to triggered)
                logger.warning(f"⚠️ ALERT: {device.hostname} Interface {interface.if_name} has high discard rate: {discard_rate:.3f}% (threshold: {interface.packet_drop_threshold}%)")

                # Determine severity based on discard rate
                severity = "Critical" if discard_rate >= 5.0 else "High" if discard_rate >= 1.0 else "Warning"

                # Create alert history record
                alert_record = AlertHistoryService.create_alert_record(
                    db=db,
                    alert_type="packet_drop",
                    severity=severity,
                    device_id=device.id,
                    interface_id=interface.id,
                    metric_value=f"{discard_rate:.2f}%",
                    threshold_value=f">{interface.packet_drop_threshold}%",
                    message=f"Interface {interface.if_name} discard rate exceeded threshold"
                )

                interface.packet_drop_alert_state = "triggered"
                interface.packet_drop_alert_sent = True
                db.add(interface)
                return (f"Interface {interface.if_name} ({interface.if_index}) has high discard rate: {discard_rate:.3f}% (threshold: {interface.packet_drop_threshold}%)", alert_record)
            elif interface.packet_drop_alert_state == "triggered":
                pass
            elif interface.packet_drop_alert_state == "acknowledged":
                pass
        else:
            if interface.packet_drop_alert_state in ["triggered", "acknowledged"]:
                logger.info(f"✅ RECOVERY: {device.hostname} Interface {interface.if_name} discard rate normal: {discard_rate:.3f}%")

                # Find and close alert history record
                alert_record = AlertHistoryService.get_active_alert_record(
                    db=db,
                    alert_type="packet_drop",
                    device_id=device.id,
                    interface_id=interface.id
                )
                if alert_record:
                    AlertHistoryService.record_auto_clear(
                        db=db,
                        alert_record=alert_record,
                        message=f"Interface {interface.if_name} discard rate returned to normal: {discard_rate:.3f}%"
                    )

                interface.packet_drop_alert_state = "clear"
                interface.packet_drop_acknowledged_at = None
                interface.packet_drop_alert_sent = False
                db.add(interface)
                return (f"Interface {interface.if_name} ({interface.if_index}) discard rate is normal: {discard_rate:.3f}%", None)

        return None