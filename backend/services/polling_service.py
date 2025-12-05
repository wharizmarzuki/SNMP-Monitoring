"""
Device and interface metrics collection via SNMP polling.
Handles concurrent polling with session isolation and alert evaluation.
"""
import asyncio
import typing
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core import database, models, schemas
from services.snmp_service import get_snmp_data, bulk_snmp_walk, SNMPClient, get_snmp_client
from services.device_service import SQLAlchemyDeviceRepository, insert_device_metric
from services.alert_service import AlertEvaluator
from app.config.settings import settings, get_runtime_settings
from app.config.logging import logger


def calculate_interface_speed(raw_data: dict) -> tuple[int | None, str | None]:
    """
    Determine interface speed from SNMP data using ifHighSpeed or ifSpeed.
    Returns (speed_bps, speed_source) tuple.

    Priority:
    1. ifHighSpeed (for Gigabit+ interfaces, reports in Mbps)
    2. ifSpeed (for slower interfaces, reports in bps, max ~4 Gbps)
    """
    # Try ifHighSpeed first (IF-MIB::ifHighSpeed, in Mbps)
    high_speed_key = schemas.INTERFACE_OIDS.get("interface_high_speed")
    if high_speed_key:
        high_speed_mbps = raw_data.get(high_speed_key)
        if high_speed_mbps:
            try:
                high_speed_int = int(high_speed_mbps)
                if high_speed_int > 0:
                    # Convert Mbps to bps
                    speed_bps = high_speed_int * 1_000_000
                    return speed_bps, "ifHighSpeed"
            except (ValueError, TypeError):
                pass

    # Fallback to ifSpeed (reports in bps, from standard IF-MIB ifTable)
    speed_key = schemas.INTERFACE_OIDS["interface_speed"]
    speed_bps = raw_data.get(speed_key)

    if speed_bps:
        try:
            speed_int = int(speed_bps)
            # ifSpeed maxes out at 4,294,967,295 (2^32-1)
            # If value is exactly this, it's likely capped; try to use ifHighSpeed
            if speed_int > 0 and speed_int < 4_294_967_295:
                return speed_int, "ifSpeed"
        except (ValueError, TypeError):
            pass

    # Speed not available
    return None, None


def clear_interface_alerts(device: models.Device, db: Session):
    """Clear all interface alerts when device becomes unreachable."""
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


async def poll_device(
    device: models.Device,
    client: SNMPClient,
    db: Session,
    poll_time: datetime | None = None
) -> bool:
    """
    Poll device for CPU/memory metrics and evaluate alerts.
    Returns True if poll succeeded, False otherwise.

    Args:
        device: Device to poll
        client: SNMP client
        db: Database session
        poll_time: Optional explicit timestamp for polling cycle synchronization
    """
    host = typing.cast(str, device.ip_address)
    vendor = typing.cast(str, device.vendor)
    repo = SQLAlchemyDeviceRepository(db)

    # Use provided poll_time or generate one if not provided (for backwards compatibility)
    if poll_time is None:
        poll_time = datetime.now(timezone.utc)

    # Mark poll attempt timestamp
    device.last_poll_attempt = poll_time

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
        device.last_poll_success = poll_time
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
            # Use Pool 1 (Processor Memory) - available on all Cisco devices
            used_mem = float(vendor_data.get("memory_pool_used", 0))
            free_mem = float(vendor_data.get("memory_pool_free", 0))
            total_mem = used_mem + free_mem
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
        await insert_device_metric(metric_schema, repo, timestamp=poll_time) # Pass explicit timestamp

        db.add(device)  # Save the updated device state

        return True

    except Exception as e:
        logger.error(f"Error in poll_device for {host}: {e}")
        device.consecutive_failures += 1
        db.add(device)
        db.rollback()
        return False


async def poll_interfaces(
    device: models.Device,
    client: SNMPClient,
    db: Session,
    poll_time: datetime | None = None
):
    """
    Poll all interfaces for metrics and evaluate alerts.

    Args:
        device: Device to poll
        client: SNMP client
        db: Database session
        poll_time: Optional explicit timestamp for polling cycle synchronization
    """
    host = typing.cast(str, device.ip_address)

    # Use provided poll_time or generate one if not provided (for backwards compatibility)
    # When called from perform_full_poll(), this will be the shared cycle timestamp
    if poll_time is None:
        poll_time = datetime.now(timezone.utc)

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

            # Calculate interface speed from SNMP data
            speed_bps, speed_source = calculate_interface_speed(raw)

            # Log speed detection for debugging
            if speed_bps is None:
                logger.debug(f"No speed detected for interface {if_name} (index {idx}) on {host}")
            else:
                logger.debug(f"Interface {if_name} (index {idx}) on {host}: {speed_bps:,} bps ({speed_bps/1_000_000:.1f} Mbps) from {speed_source}")

            if idx not in existing_interfaces:
                db_interface = models.Interface(
                    device_id=device.id,
                    if_index=idx,
                    if_name=if_name,
                    speed_bps=speed_bps,
                    speed_source=speed_source,
                    speed_last_updated=datetime.now(timezone.utc) if speed_bps else None
                )
                db.add(db_interface)
                db.flush()
                existing_interfaces[idx] = db_interface
            else:
                db_interface = existing_interfaces[idx]
                # Update speed if it changed or hasn't been set
                if speed_bps is not None and (
                    db_interface.speed_bps != speed_bps or
                    db_interface.speed_bps is None
                ):
                    db_interface.speed_bps = speed_bps
                    db_interface.speed_source = speed_source
                    db_interface.speed_last_updated = datetime.now(timezone.utc)
                    db.add(db_interface)

            metric = models.InterfaceMetric(
                interface_id=db_interface.id,
                timestamp=poll_time,  # Explicit timestamp for all interfaces in this poll cycle
                admin_status=int(raw.get(schemas.INTERFACE_OIDS["interface_admin_status"], 0)),
                oper_status=int(raw.get(schemas.INTERFACE_OIDS["interface_operational_status"], 0)),
                # Cast to int for BigInteger columns (prevents precision loss on high-speed interfaces)
                octets_in=int(float(raw.get(schemas.INTERFACE_OIDS["inbound_octets"], 0))),
                octets_out=int(float(raw.get(schemas.INTERFACE_OIDS["outbound_octets"], 0))),
                errors_in=int(float(raw.get(schemas.INTERFACE_OIDS["inbound_errors"], 0))),
                errors_out=int(float(raw.get(schemas.INTERFACE_OIDS["outbound_errors"], 0))),
                discards_in=int(float(raw.get(schemas.INTERFACE_OIDS["inbound_discards"], 0))),
                discards_out=int(float(raw.get(schemas.INTERFACE_OIDS["outbound_discards"], 0))),
                # Packet counters for accurate discard rate calculation (discards are packet-based)
                packets_in=int(float(raw.get(schemas.INTERFACE_OIDS.get("inbound_packets", "0"), 0))),
                packets_out=int(float(raw.get(schemas.INTERFACE_OIDS.get("outbound_packets", "0"), 0))),
            )

            db.add(metric)

        db.flush()

        AlertEvaluator.evaluate_interfaces(device, db)

    except Exception as e:
        logger.error(f"Error in poll_interfaces for {host}: {e}")



async def perform_full_poll(db: Session, client: SNMPClient):
    """
    Poll all devices with session isolation.
    Each concurrent polling task gets its own database session.
    All devices in this polling cycle will share the same timestamp.
    """
    logger.info("Starting scheduled full poll...")
    try:
        # Get runtime settings (database takes priority over .env)
        runtime_config = get_runtime_settings(db)
        polling_concurrency = runtime_config["polling_concurrency"]

        # Use main session only to fetch device IDs (read-only operation)
        all_devices = db.query(models.Device).all()
        device_ids = [d.id for d in all_devices]

        if not device_ids:
            logger.info("No devices in database to poll.")
            return

        semaphore = asyncio.Semaphore(polling_concurrency)
        successful_polls = 0
        failed_polls = 0

        # Capture single timestamp for this entire polling cycle
        # This ensures all devices and interfaces get the same timestamp for proper aggregation
        polling_cycle_timestamp = datetime.now(timezone.utc)
        logger.debug(f"Polling cycle timestamp: {polling_cycle_timestamp.isoformat()}")

        async def limited_polling(device_id: int):
            """
            Poll single device with dedicated database session.
            """
            nonlocal successful_polls, failed_polls

            async with semaphore:
                task_db = database.SessionLocal()
                try:
                    device = task_db.query(models.Device).filter_by(id=device_id).first()
                    if not device:
                        logger.warning(f"Device with ID {device_id} not found")
                        return

                    # Pass polling cycle timestamp for synchronization
                    poll_succeeded = await poll_device(device, client, task_db, poll_time=polling_cycle_timestamp)

                    if poll_succeeded:
                        # Pass polling cycle timestamp for synchronization
                        await poll_interfaces(device, client, task_db, poll_time=polling_cycle_timestamp)
                        successful_polls += 1
                    else:
                        if not device.is_reachable:
                            clear_interface_alerts(device, task_db)
                            logger.debug(f"Skipped interface poll for unreachable device {device.ip_address}")
                        failed_polls += 1

                    task_db.commit()

                except Exception as e:
                    logger.error(f"Error polling device {device_id}: {e}")
                    task_db.rollback()
                    failed_polls += 1
                finally:
                    task_db.close()

        tasks = [limited_polling(device_id) for device_id in device_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Poll complete: {successful_polls} successful, {failed_polls} failed out of {len(device_ids)} devices.")

    except Exception as e:
        logger.error(f"Error during scheduled poll: {e}")