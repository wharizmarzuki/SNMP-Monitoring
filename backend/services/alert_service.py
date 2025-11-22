from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core import models
from app.config.logging import logger
from services.email_service import send_email_background

class AlertEvaluator:
    
    @staticmethod
    def _notify(subject: str, body: str, db: Session):
        """Helper to fetch recipients and call email service"""
        # 1. Get recipients from DB
        recipients_db = db.query(models.AlertRecipient).all()
        recipient_list = [r.email for r in recipients_db]
        
        if not recipient_list:
            logger.warning(f"⚠️ Alert triggered but no recipients found in DB!")
            return

        # 2. Send the email
        send_email_background(subject, body, recipient_list)

    @staticmethod
    def evaluate_cpu(device: models.Device, current_val: float, db: Session):
        """
        Evaluates CPU with state-based alert management (Phase 2).
        Supports maintenance mode and acknowledgment.
        """
        # Check maintenance mode first
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
            # Threshold exceeded
            if device.cpu_alert_state == "clear":
                # First time exceeding, send alert
                logger.warning(f"⚠️ ALERT: {device.hostname} High CPU: {current_val}%")

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                exceeded_by = round(current_val - device.cpu_threshold, 2)

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

                AlertEvaluator._notify(subject, body, db)

                device.cpu_alert_state = "triggered"
                device.cpu_alert_sent = True  # Keep legacy flag in sync
                is_triggered = True
            elif device.cpu_alert_state == "triggered":
                # Already alerted, still high - no action (no spam)
                pass
            elif device.cpu_alert_state == "acknowledged":
                # User acknowledged, still high - no action (user knows)
                pass
        else:
            # Threshold normal
            if device.cpu_alert_state in ["triggered", "acknowledged"]:
                # Was in alert, now recovered
                logger.info(f"✅ RECOVERY: {device.hostname} CPU Normal")

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
                device.cpu_acknowledged_at = None  # Reset acknowledgment
                device.cpu_alert_sent = False  # Keep legacy flag in sync
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_memory(device: models.Device, current_val: float, db: Session):
        """
        Evaluates Memory with state-based alert management (Phase 2).
        Supports maintenance mode and acknowledgment.
        """
        # Check maintenance mode first
        if device.maintenance_mode and device.maintenance_until:
            if datetime.now(timezone.utc) < device.maintenance_until:
                return False  # Suppress all alerts during maintenance

        is_triggered = False

        if current_val > device.memory_threshold:
            # Threshold exceeded
            if device.memory_alert_state == "clear":
                # First time exceeding, send alert
                logger.warning(f"⚠️ ALERT: {device.hostname} High Memory: {current_val}%")

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                exceeded_by = round(current_val - device.memory_threshold, 2)

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

                AlertEvaluator._notify(subject, body, db)

                device.memory_alert_state = "triggered"
                device.memory_alert_sent = True  # Keep legacy flag in sync
                is_triggered = True
            elif device.memory_alert_state == "triggered":
                # Already alerted, still high - no action
                pass
            elif device.memory_alert_state == "acknowledged":
                # User acknowledged, still high - no action
                pass
        else:
            # Threshold normal
            if device.memory_alert_state in ["triggered", "acknowledged"]:
                # Was in alert, now recovered
                logger.info(f"✅ RECOVERY: {device.hostname} Memory Normal")

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
                device.memory_acknowledged_at = None  # Reset acknowledgment
                device.memory_alert_sent = False  # Keep legacy flag in sync
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_reachability(device: models.Device, db: Session):
        """
        Evaluates device reachability with state-based alert management (Phase 2).
        Supports maintenance mode and acknowledgment.

        Returns:
            bool: True if alert state changed, False otherwise
        """
        # Check maintenance mode first
        if device.maintenance_mode and device.maintenance_until:
            if datetime.now(timezone.utc) < device.maintenance_until:
                return False  # Suppress all alerts during maintenance

        is_triggered = False

        if not device.is_reachable:
            # Device is UNREACHABLE
            if device.reachability_alert_state == "clear":
                # First time unreachable, send alert
                logger.error(
                    f"🔴 ALERT: {device.hostname} ({device.ip_address}) is UNREACHABLE "
                    f"after {device.consecutive_failures} consecutive failures"
                )

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                last_success = device.last_poll_success.strftime("%Y-%m-%d %H:%M:%S UTC") if device.last_poll_success else "Never"
                last_attempt = device.last_poll_attempt.strftime("%Y-%m-%d %H:%M:%S UTC") if device.last_poll_attempt else "Unknown"

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

                AlertEvaluator._notify(subject, body, db)

                device.reachability_alert_state = "triggered"
                device.reachability_alert_sent = True  # Keep legacy flag in sync
                is_triggered = True
            elif device.reachability_alert_state == "triggered":
                # Already alerted, still unreachable - no action
                pass
            elif device.reachability_alert_state == "acknowledged":
                # User acknowledged, still unreachable - no action
                pass
        else:
            # Device is REACHABLE
            if device.reachability_alert_state in ["triggered", "acknowledged"]:
                # Was unreachable, now recovered
                logger.info(
                    f"✅ RECOVERY: {device.hostname} ({device.ip_address}) is REACHABLE again"
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
                device.reachability_acknowledged_at = None  # Reset acknowledgment
                device.reachability_alert_sent = False  # Keep legacy flag in sync
                is_triggered = True

        return is_triggered

    @staticmethod
    def evaluate_interfaces(device: models.Device, db: Session):
        """
        Checks all interfaces for Down status or Packet Drops.
        This function now aggregates alerts before sending.
        """
        alerts_triggered = []
        recoveries_triggered = []
        
        for interface in device.interfaces:
            # Get the last two metrics to check for state changes
            metrics = db.query(models.InterfaceMetric)\
                .filter(models.InterfaceMetric.interface_id == interface.id)\
                .order_by(models.InterfaceMetric.timestamp.desc())\
                .limit(2)\
                .all()
                
            if not metrics:
                continue # No metrics for this interface yet

            latest_metric = metrics[0]
            previous_metric = metrics[1] if len(metrics) > 1 else None

            # 1. Check Operational Status
            status_msg = AlertEvaluator._check_oper_status(
                device, interface, latest_metric, previous_metric, db
            )
            if status_msg:
                if "DOWN" in status_msg:
                    alerts_triggered.append(status_msg)
                else: # "UP"
                    recoveries_triggered.append(status_msg)
            
            # 2. Check Packet Drops
            drop_msg = AlertEvaluator._check_packet_drops(
                device, interface, latest_metric, previous_metric, db
            )
            if drop_msg:
                if "high packet" in drop_msg:
                    alerts_triggered.append(drop_msg)
                else: # "normal"
                    recoveries_triggered.append(drop_msg)

        # --- Send Bundled Emails ---
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

            AlertEvaluator._notify(subject, body, db)

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
    ) -> str | None:
        """
        Checks for UP/DOWN state changes with state-based alert management (Phase 2).
        Returns a message string if a notifiable event occurred, else None.
        """
        is_down = (latest_metric.oper_status != 1) # 1 = up

        if is_down:
            if interface.oper_status_alert_state == "clear":
                # It's DOWN and state is CLEAR. Only alert if it *changed* to DOWN.
                if previous_metric is not None:
                    prev_is_down = (previous_metric.oper_status != 1)
                    if not prev_is_down:
                        # State change: UP -> DOWN
                        logger.warning(f"⚠️ ALERT: {device.hostname} Interface {interface.if_name} is DOWN")
                        interface.oper_status_alert_state = "triggered"
                        interface.oper_status_alert_sent = True  # Keep legacy flag in sync
                        db.add(interface)
                        return f"Interface {interface.if_name} ({interface.if_index}) is DOWN"
            elif interface.oper_status_alert_state == "triggered":
                # Already alerted, still down - no action
                pass
            elif interface.oper_status_alert_state == "acknowledged":
                # User acknowledged, still down - no action
                pass
        else:
            # It's UP.
            if interface.oper_status_alert_state in ["triggered", "acknowledged"]:
                # State change: DOWN -> UP (Recovery)
                logger.info(f"✅ RECOVERY: {device.hostname} Interface {interface.if_name} is UP")
                interface.oper_status_alert_state = "clear"
                interface.oper_status_acknowledged_at = None  # Reset acknowledgment
                interface.oper_status_alert_sent = False  # Keep legacy flag in sync
                db.add(interface)
                return f"Interface {interface.if_name} ({interface.if_index}) is UP"

        return None # No state change or event to notify

    @staticmethod
    def _check_packet_drops(
        device: models.Device,
        interface: models.Interface,
        latest_metric: models.InterfaceMetric,
        previous_metric: models.InterfaceMetric | None,
        db: Session
    ) -> str | None:
        """
        Checks for discard rate threshold breaches with state-based alert management (Phase 2).
        Compares discard rate (percentage) against threshold (percentage).
        Returns a message string if a notifiable event occurred, else None.
        """
        # Calculate discard rate as percentage
        total_drops = (latest_metric.discards_in or 0) + (latest_metric.discards_out or 0)
        total_traffic = (latest_metric.octets_in or 0) + (latest_metric.octets_out or 0)
        discard_rate = (total_drops / total_traffic * 100) if total_traffic > 0 else 0

        is_exceeded = (discard_rate > interface.packet_drop_threshold)

        if is_exceeded:
            if interface.packet_drop_alert_state == "clear":
                # It's EXCEEDED and state is CLEAR. Only alert if it *changed*.
                if previous_metric is not None:
                    prev_total_drops = (previous_metric.discards_in or 0) + (previous_metric.discards_out or 0)
                    prev_total_traffic = (previous_metric.octets_in or 0) + (previous_metric.octets_out or 0)
                    prev_discard_rate = (prev_total_drops / prev_total_traffic * 100) if prev_total_traffic > 0 else 0
                    prev_is_exceeded = (prev_discard_rate > interface.packet_drop_threshold)

                    if not prev_is_exceeded:
                        # State change: OK -> DROPPING
                        logger.warning(f"⚠️ ALERT: {device.hostname} Interface {interface.if_name} has high discard rate: {discard_rate:.3f}% (threshold: {interface.packet_drop_threshold}%)")
                        interface.packet_drop_alert_state = "triggered"
                        interface.packet_drop_alert_sent = True  # Keep legacy flag in sync
                        db.add(interface)
                        return f"Interface {interface.if_name} ({interface.if_index}) has high discard rate: {discard_rate:.3f}% (threshold: {interface.packet_drop_threshold}%)"
            elif interface.packet_drop_alert_state == "triggered":
                # Already alerted, still exceeding - no action
                pass
            elif interface.packet_drop_alert_state == "acknowledged":
                # User acknowledged, still exceeding - no action
                pass
        else:
            # It's NOT exceeded.
            if interface.packet_drop_alert_state in ["triggered", "acknowledged"]:
                # State change: DROPPING -> OK (Recovery)
                logger.info(f"✅ RECOVERY: {device.hostname} Interface {interface.if_name} discard rate normal: {discard_rate:.3f}%")
                interface.packet_drop_alert_state = "clear"
                interface.packet_drop_acknowledged_at = None  # Reset acknowledgment
                interface.packet_drop_alert_sent = False  # Keep legacy flag in sync
                db.add(interface)
                return f"Interface {interface.if_name} ({interface.if_index}) discard rate is normal: {discard_rate:.3f}%"

        return None