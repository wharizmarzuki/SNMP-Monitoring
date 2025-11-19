import asyncio
import typing
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core import database, models, schemas
from services.snmp_service import get_snmp_data, bulk_snmp_walk, SNMPClient, get_snmp_client
from services.device_service import SQLAlchemyDeviceRepository, insert_device_metric
from services.alert_service import AlertEvaluator
from app.config.settings import settings
from app.config.logging import logger

# ---
# THIS IS THE LOGIC THAT WAS INCORRECTLY IN YOUR API FILE.
# IT NOW LIVES IN THE SERVICE LAYER.
# ---

def clear_interface_alerts(device: models.Device, db: Session):
    """
    Clear all interface alert states when device becomes unreachable (Phase 2).

    This prevents stale interface alerts from showing in the dashboard
    when we can't verify interface status due to device being down.
    """
    for interface in device.interfaces:
        if (interface.oper_status_alert_state != "clear" or
            interface.packet_drop_alert_state != "clear"):
            # Clear state-based alerts
            interface.oper_status_alert_state = "clear"
            interface.oper_status_acknowledged_at = None
            interface.packet_drop_alert_state = "clear"
            interface.packet_drop_acknowledged_at = None

            # Clear legacy flags for backward compatibility
            interface.oper_status_alert_sent = False
            interface.packet_drop_alert_sent = False

            db.add(interface)
            logger.debug(f"Cleared alerts for interface {interface.if_name} on unreachable device {device.ip_address}")


async def poll_device(device: models.Device, client: SNMPClient, db: Session) -> bool:
    """
    Polls a single device for CPU/Memory and checks alerts.

    Returns:
        bool: True if poll succeeded, False if poll failed
    """
    host = typing.cast(str, device.ip_address)
    vendor = typing.cast(str, device.vendor)
    repo = SQLAlchemyDeviceRepository(db) # Create repo once

    # Mark poll attempt timestamp
    device.last_poll_attempt = datetime.now(timezone.utc)

    try:
        oids = list(schemas.DEVICE_OIDS.values()) + list(schemas.VENDOR_OIDS.get(vendor, {}).values())
        result = await get_snmp_data(host, oids, client)

        if not (result and result.get("success")):
            logger.warning(f"SNMP poll failed for {host}")

            # Track failure
            device.consecutive_failures += 1

            # Mark as unreachable after failure_threshold consecutive failures
            if device.consecutive_failures >= device.failure_threshold and device.is_reachable:
                device.is_reachable = False
                logger.error(f"Device {host} marked as UNREACHABLE after {device.consecutive_failures} failures")

            # Evaluate reachability alert
            reachability_changed = AlertEvaluator.evaluate_reachability(device, db)
            if reachability_changed:
                db.add(device)  # Save alert flag changes

            db.add(device)  # Save the failure state
            return False

        # Poll succeeded - reset failure counters
        device.last_poll_success = datetime.now(timezone.utc)
        device.consecutive_failures = 0

        # Mark as reachable if it was previously down
        if not device.is_reachable:
            device.is_reachable = True
            logger.info(f"Device {host} is REACHABLE again")

        # Evaluate reachability alert
        reachability_changed = AlertEvaluator.evaluate_reachability(device, db)
        if reachability_changed:
            db.add(device)  # Save alert flag changes

        data = result["data"]
        oid_values = {}

        device_oids_list = list(schemas.DEVICE_OIDS.items())
        for i, (key, oid) in enumerate(device_oids_list):
            oid_values[key] = data[i]["value"] if i < len(data) else None

        oid_values["device_id"] = device.id

        vendor_oids = schemas.VENDOR_OIDS.get(vendor, {})
        vendor_data = {}
        oid_to_value = {item["oid"]: item["value"] for item in data}

        for key, oid in vendor_oids.items():
            vendor_data[key] = oid_to_value.get(oid, "0")

        # Calculate CPU
        cpu_val = float(vendor_data.get("cpu_utilization", "0"))
        oid_values["cpu_utilization"] = cpu_val

        # Calculate Memory
        mem_val = 0.0
        if vendor == "Cisco":
            pool_1 = float(vendor_data.get("memory_pool_1", 0))
            pool_2 = float(vendor_data.get("memory_pool_2", 0))
            used_mem = float(vendor_data.get("memory_pool_13", 0))
            total_mem = pool_1 + pool_2
            if total_mem > 0:
                mem_val = (used_mem / total_mem) * 100
        oid_values["memory_utilization"] = mem_val

        # --- Alert Evaluation (Inline) ---
        cpu_changed = AlertEvaluator.evaluate_cpu(device, cpu_val, db)
        mem_changed = AlertEvaluator.evaluate_memory(device, mem_val, db)
        if cpu_changed or mem_changed:
            db.add(device) # Add the device to the session to save its new alert state

        # --- Save Metric ---
        metric_schema = schemas.DeviceMetrics.model_validate(oid_values)
        await insert_device_metric(metric_schema, repo) # This will db.add()

        db.add(device)  # Save the updated device state

        return True

    except Exception as e:
        logger.error(f"Error in poll_device for {host}: {e}")
        device.consecutive_failures += 1
        db.add(device)
        db.rollback()
        return False


async def poll_interfaces(device: models.Device, client: SNMPClient, db: Session):
    """Polls all interfaces for a single device, stores metrics, and evaluates alerts."""
    host = typing.cast(str, device.ip_address)

    try:
        oids = list(schemas.INTERFACE_OIDS.values())
        result = await bulk_snmp_walk(host, oids, client)

        if not (result and result.get("success")):
            logger.warning(f"Interface poll failed for {host}")
            return

        interfaces_data = {}
        for item in result["data"]:
            index = item["index"]
            interfaces_data.setdefault(index, {})
            interfaces_data[index][item["base_oid"]] = item["value"]

        existing_interfaces = {
            iface.if_index: iface for iface in
            db.query(models.Interface).filter_by(device_id=device.id).all()
        }

        for index, raw in interfaces_data.items():
            idx = int(index)
            if_name = raw.get(schemas.INTERFACE_OIDS["interface_description"], "n/a")

            if idx not in existing_interfaces:
                db_interface = models.Interface(
                    device_id=device.id,
                    if_index=idx,
                    if_name=if_name
                )
                db.add(db_interface)
                db.flush()        
                existing_interfaces[idx] = db_interface
            else:
                db_interface = existing_interfaces[idx]

            metric = models.InterfaceMetric(
                interface_id=db_interface.id,
                admin_status=int(raw.get(schemas.INTERFACE_OIDS["interface_admin_status"], 0)),
                oper_status=int(raw.get(schemas.INTERFACE_OIDS["interface_operational_status"], 0)),
                octets_in=float(raw.get(schemas.INTERFACE_OIDS["inbound_octets"], 0)),
                octets_out=float(raw.get(schemas.INTERFACE_OIDS["outbound_octets"], 0)),
                errors_in=float(raw.get(schemas.INTERFACE_OIDS["inbound_errors"], 0)),
                errors_out=float(raw.get(schemas.INTERFACE_OIDS["outbound_errors"], 0)),
                discards_in=float(raw.get(schemas.INTERFACE_OIDS["inbound_discards"], 0)),
                discards_out=float(raw.get(schemas.INTERFACE_OIDS["outbound_discards"], 0)),
            )

            db.add(metric)

        db.flush()

        AlertEvaluator.evaluate_interfaces(device, db)

    except Exception as e:
        logger.error(f"Error in poll_interfaces for {host}: {e}")



async def perform_full_poll(db: Session, client: SNMPClient):
    """
    This is the core logic, extracted from your old API endpoint.
    It fetches all devices and runs the polling tasks.
    """
    logger.info("Starting scheduled full poll...")
    try:
        all_devices = db.query(models.Device).all()
        if not all_devices:
            logger.info("No devices in database to poll.")
            return

        semaphore = asyncio.Semaphore(settings.polling_concurrency)

        async def limited_polling(device: models.Device):
            async with semaphore:
                poll_succeeded = await poll_device(device, client, db)

                if poll_succeeded:
                    # Only poll interfaces if device poll succeeded
                    await poll_interfaces(device, client, db)
                else:
                    # Clear interface alerts when device is unreachable
                    if not device.is_reachable:
                        clear_interface_alerts(device, db)
                        logger.debug(f"Skipped interface poll for unreachable device {device.ip_address}")

        tasks = [limited_polling(device) for device in all_devices]
        await asyncio.gather(*tasks)
        
        db.commit()
        logger.info(f"Poll complete and data committed for {len(all_devices)} devices.")

    except Exception as e:
        logger.error(f"Error during scheduled poll: {e}")
        db.rollback()