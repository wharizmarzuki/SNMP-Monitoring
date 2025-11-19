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

                subject = f"🔥 CPU Alert: {device.hostname}"
                body = (f"Critical Alert on {device.hostname} ({device.ip_address})\n\n"
                        f"Current CPU: {current_val}%\n"
                        f"Threshold: {device.cpu_threshold}%")

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

                subject = f"✅ CPU Recovered: {device.hostname}"
                body = f"CPU usage on {device.hostname} has returned to normal ({current_val}%)."

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

                subject = f"🔥 Memory Alert: {device.hostname}"
                body = (f"Critical Alert on {device.hostname} ({device.ip_address})\n\n"
                        f"Current Memory: {current_val}%\n"
                        f"Threshold: {device.memory_threshold}%")

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

                subject = f"✅ Memory Recovered: {device.hostname}"
                body = f"Memory usage on {device.hostname} has returned to normal ({current_val}%)."

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

                subject = f"🔴 Device Unreachable: {device.hostname}"
                body = (
                    f"Critical Alert: Device is UNREACHABLE\n\n"
                    f"Device: {device.hostname}\n"
                    f"IP Address: {device.ip_address}\n"
                    f"Consecutive Failures: {device.consecutive_failures}\n"
                    f"Last Successful Poll: {device.last_poll_success}\n"
                    f"Last Poll Attempt: {device.last_poll_attempt}\n\n"
                    f"The device has failed to respond to SNMP polls. "
                    f"Please check network connectivity and device status."
                )

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

                subject = f"✅ Device Recovered: {device.hostname}"
                body = (
                    f"Recovery Alert: Device is REACHABLE\n\n"
                    f"Device: {device.hostname}\n"
                    f"IP Address: {device.ip_address}\n"
                    f"Last Successful Poll: {device.last_poll_success}\n\n"
                    f"The device is responding to SNMP polls again."
                )

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
            subject = f"🔥 Interface Alert(s) for {device.hostname}"
            body = f"The following interface alerts were triggered on {device.hostname} ({device.ip_address}):\n\n"
            body += "\n".join(f"- {msg}" for msg in alerts_triggered)
            AlertEvaluator._notify(subject, body, db)

        if recoveries_triggered:
            subject = f"✅ Interface Recovery for {device.hostname}"
            body = f"The following interface recoveries occurred on {device.hostname} ({device.ip_address}):\n\n"
            body += "\n".join(f"- {msg}" for msg in recoveries_triggered)
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