import ipaddress
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import Depends, APIRouter, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.core import database, models
from app.core import schemas
from app.core.exceptions import DeviceNotFoundError, InterfaceNotFoundError, AlertNotFoundError, DiscoveryError
from app.core.cache import cache
from app.core.security import get_current_user
from services import device_service, snmp_service
from services.device_service import DeviceRepository, get_repository
from services.snmp_service import SNMPClient, get_snmp_client
from app.config.logging import logger
from services.discovery_service import perform_full_discovery

router = APIRouter(
    prefix="/device",
    tags=["Device"],
    dependencies=[Depends(get_current_user)]  # Require authentication for all device endpoints
)


@router.get("/discover", response_model=schemas.DiscoveryResponse)
async def discovery_api(
    network: str = "192.168.254.1",
    subnet: str = "27",
    db: Session = Depends(database.get_db)
):
    """
    API Endpoint to manually trigger a full network discovery.
    """
    logger.info("Manual discovery triggered via API...")
    try:
        # Get SNMP client with runtime settings from database
        client = get_snmp_client(db)

        # --- THIS ENDPOINT IS NOW A SIMPLE WRAPPER ---
        result_data = await perform_full_discovery(db, client, network, subnet)
        
        # Convert SQLAlchemy models to Pydantic schemas for the response
        pydantic_devices = [schemas.DeviceInfo.model_validate(dev) for dev in result_data["devices"]]

        return schemas.DiscoveryResponse(
            total_scanned=result_data["total_scanned"],
            devices_found=result_data["devices_found"],
            devices=pydantic_devices,
        )
    except Exception as e:
        logger.error(f"Error during manual discovery: {e}")
        raise DiscoveryError(str(e))


@router.post("/", response_model=None)
async def create_device_endpoint(
    device_info: schemas.DeviceInfo,
    validate: bool = True,
    repo: DeviceRepository = Depends(get_repository),
    db: Session = Depends(database.get_db)
):
    """
    Create a new device with optional SNMP validation.

    By default (validate=True), the endpoint will attempt to reach the device
    via SNMP before adding it to prevent adding unreachable devices.

    Set validate=false to skip validation (not recommended).
    """
    if validate:
        # Get SNMP client with runtime settings from database
        client = get_snmp_client(db)

        # Try to reach device via SNMP first
        logger.info(f"Validating SNMP connectivity to {device_info.ip_address}...")
        try:
            # Query sysDescr (1.3.6.1.2.1.1.1.0) as basic connectivity test
            sys_descr = await client.get(device_info.ip_address, ["1.3.6.1.2.1.1.1.0"])
            if not sys_descr:
                raise HTTPException(
                    status_code=400,
                    detail=f"Device {device_info.ip_address} is not reachable via SNMP. Check IP address, SNMP community string, and network connectivity."
                )
            logger.info(f"SNMP validation successful for {device_info.ip_address}")
        except Exception as e:
            logger.error(f"SNMP validation failed for {device_info.ip_address}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"SNMP validation failed: {str(e)}. Device may be unreachable or SNMP may be disabled."
            )

    try:
        await device_service.create_device(device_info, repo)
        return {"message": "Device created successfully"}
    except Exception as e:
        logger.error(f"Error creating device {device_info.ip_address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.DeviceResponse])
async def get_all_devices_endpoint(
    repo: DeviceRepository = Depends(get_repository)
):
    """Get all devices with stable DTO response"""
    devices = device_service.get_all_devices(repo)
    return [schemas.DeviceResponse.model_validate(device) for device in devices]

@router.get("/{ip}", response_model=schemas.DeviceResponse)
async def get_devices_endpoint(
    ip: str,
    repo: DeviceRepository = Depends(get_repository)
):
    """Get device by IP with stable DTO response"""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)
    return schemas.DeviceResponse.model_validate(device)

@router.delete("/{ip}")
async def delete_devices_endpoint(
    ip: str,
    repo: DeviceRepository = Depends(get_repository)
):
    # This function remains unchanged
    device_service.delete_device(ip, repo)
    return {"message": "Device deleted"}


@router.put("/{ip}/thresholds", response_model=schemas.DeviceResponse)
async def update_device_thresholds_batch(
    ip: str,
    thresholds: schemas.ThresholdBatchUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Batch update all thresholds for a device.

    This endpoint allows updating multiple thresholds in a single request,
    matching the frontend payload structure. Only provided thresholds will be updated.
    """
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    # Update only provided thresholds
    if thresholds.cpu_threshold is not None:
        device.cpu_threshold = thresholds.cpu_threshold
    if thresholds.memory_threshold is not None:
        device.memory_threshold = thresholds.memory_threshold
    if thresholds.failure_threshold is not None:
        device.failure_threshold = thresholds.failure_threshold

    repo.db.commit()
    repo.db.refresh(device)

    # Invalidate related caches
    cache.delete(f"device:{ip}")
    cache.delete("network_summary")
    cache.delete_pattern("top_devices:*")

    return schemas.DeviceResponse.model_validate(device)


@router.put("/{ip}/interface/{if_index}/threshold", response_model=schemas.InterfaceThresholdResponse)
async def update_interface_threshold_endpoint(
    ip: str,
    if_index: int,
    threshold_data: schemas.InterfaceThresholdUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Update the discard rate threshold for a specific interface.
    Threshold is a percentage (0-100) of total traffic that triggers alerts.
    Example: 0.1 means alert when discard rate exceeds 0.1% of traffic.
    """
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()
    
    if not interface:
        raise InterfaceNotFoundError(ip, if_index)

    interface.packet_drop_threshold = threshold_data.threshold_value
    repo.db.commit()
    repo.db.refresh(interface)

    return interface


# ==================== Phase 2: Alert State Management Endpoints ====================

# NEW CONSOLIDATED ENDPOINTS (Recommended)

@router.patch("/{ip}/alerts/{alert_type}", response_model=schemas.AlertStateResponse)
async def manage_device_alert(
    ip: str,
    alert_type: str,
    action_data: schemas.AlertAction,
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Consolidated endpoint for managing device alert states.

    Supports:
    - alert_type: cpu, memory, reachability
    - action: acknowledge, resolve

    Request body:
    {
        "action": "acknowledge" | "resolve",
        "notes": "optional notes",
        "reason": "optional reason (for resolve)"
    }
    """
    # Validate alert type
    alert_map = {
        "cpu": ("cpu_alert_state", "cpu_acknowledged_at", "cpu_alert_sent", "CPU"),
        "memory": ("memory_alert_state", "memory_acknowledged_at", "memory_alert_sent", "Memory"),
        "reachability": ("reachability_alert_state", "reachability_acknowledged_at", "reachability_alert_sent", "Reachability")
    }

    if alert_type not in alert_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid alert type: {alert_type}. Must be one of: {', '.join(alert_map.keys())}"
        )

    # Validate action
    if action_data.action not in ["acknowledge", "resolve"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action_data.action}. Must be 'acknowledge' or 'resolve'"
        )

    # Get device
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    state_field, ack_field, sent_field, display_name = alert_map[alert_type]
    current_state = getattr(device, state_field)

    # Perform action
    if action_data.action == "acknowledge":
        if current_state != "triggered":
            raise AlertNotFoundError(display_name)
        setattr(device, state_field, "acknowledged")
        setattr(device, ack_field, datetime.now(timezone.utc))
        message = f"{display_name} alert acknowledged"

    elif action_data.action == "resolve":
        setattr(device, state_field, "clear")
        setattr(device, ack_field, None)
        setattr(device, sent_field, False)
        message = f"{display_name} alert resolved"

    repo.db.commit()

    return schemas.AlertStateResponse(
        message=message,
        state=getattr(device, state_field),
        acknowledged_at=getattr(device, ack_field)
    )


# CONSOLIDATED INTERFACE ALERT ENDPOINT (Recommended)

@router.patch("/{ip}/interfaces/{if_index}/alerts/{alert_type}", response_model=schemas.AlertStateResponse)
async def manage_interface_alert(
    ip: str,
    if_index: int,
    alert_type: str,
    action_data: schemas.AlertAction,
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Consolidated endpoint for managing interface alert states.

    Supports:
    - alert_type: status, drops
    - action: acknowledge, resolve

    Request body:
    {
        "action": "acknowledge" | "resolve",
        "notes": "optional notes",
        "reason": "optional reason (for resolve)"
    }
    """
    # Validate alert type
    alert_map = {
        "status": ("oper_status_alert_state", "oper_status_acknowledged_at", "oper_status_alert_sent", "interface status"),
        "drops": ("packet_drop_alert_state", "packet_drop_acknowledged_at", "packet_drop_alert_sent", "packet drop")
    }

    if alert_type not in alert_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid alert type: {alert_type}. Must be one of: {', '.join(alert_map.keys())}"
        )

    # Validate action
    if action_data.action not in ["acknowledge", "resolve"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action_data.action}. Must be 'acknowledge' or 'resolve'"
        )

    # Get device and interface
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise InterfaceNotFoundError(ip, if_index)

    state_field, ack_field, sent_field, display_name = alert_map[alert_type]
    current_state = getattr(interface, state_field)

    # Perform action
    if action_data.action == "acknowledge":
        if current_state != "triggered":
            raise AlertNotFoundError(display_name)
        setattr(interface, state_field, "acknowledged")
        setattr(interface, ack_field, datetime.now(timezone.utc))
        message = f"Interface {interface.if_name} {display_name} alert acknowledged"

    elif action_data.action == "resolve":
        setattr(interface, state_field, "clear")
        setattr(interface, ack_field, None)
        setattr(interface, sent_field, False)
        message = f"Interface {interface.if_name} {display_name} alert resolved"

    repo.db.commit()

    return schemas.AlertStateResponse(
        message=message,
        state=getattr(interface, state_field),
        acknowledged_at=getattr(interface, ack_field)
    )


# ==================== Maintenance Mode Endpoint ====================

@router.put("/{ip}/maintenance")
async def update_maintenance_mode(
    ip: str,
    data: schemas.MaintenanceModeUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """Enable or disable maintenance mode for a device to suppress all alerts."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    device.maintenance_mode = data.enabled
    if data.enabled:
        device.maintenance_until = datetime.now(timezone.utc) + timedelta(minutes=data.duration_minutes)
        device.maintenance_reason = data.reason
    else:
        device.maintenance_until = None
        device.maintenance_reason = None

    repo.db.commit()

    return {
        "message": "Maintenance mode updated",
        "maintenance_mode": device.maintenance_mode,
        "maintenance_until": device.maintenance_until,
        "maintenance_reason": device.maintenance_reason
    }