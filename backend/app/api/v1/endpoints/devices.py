import ipaddress
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import Depends, APIRouter, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.core import database, models
from app.core import schemas
from services import device_service, snmp_service
from services.device_service import DeviceRepository, get_repository
from services.snmp_service import SNMPClient, get_snmp_client
from app.config.logging import logger
from services.discovery_service import perform_full_discovery

router = APIRouter(prefix="/device", tags=["Device"])


@router.get("/discover", response_model=schemas.DiscoveryResponse)
async def discovery_api(
    network: str = "192.168.254.1",
    subnet: str = "27",
    client: SNMPClient = Depends(get_snmp_client),
    db: Session = Depends(database.get_db) 
):
    """
    API Endpoint to manually trigger a full network discovery.
    """
    logger.info("Manual discovery triggered via API...")
    try:
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
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/", response_model=None)
async def create_device_endpoint(
    device_info: schemas.DeviceInfo,
    repo: DeviceRepository = Depends(get_repository) 
):
    # This function remains unchanged
    try:
        await device_service.create_device(device_info, repo)
        return {"message": "Device created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.DeviceInfo])
async def get_all_devices_endpoint(
    repo: DeviceRepository = Depends(get_repository)
):
    # This function remains unchanged
    return device_service.get_all_devices(repo)

@router.get("/{ip}", response_model=schemas.DeviceInfo)
async def get_devices_endpoint(
    ip: str,
    repo: DeviceRepository = Depends(get_repository)
):
    # This function remains unchanged
    return device_service.get_device_by_ip(ip, repo)

@router.delete("/{ip}")
async def delete_devices_endpoint(
    ip: str,
    repo: DeviceRepository = Depends(get_repository)
):
    # This function remains unchanged
    device_service.delete_device(ip, repo)
    return {"message": "Device deleted"}


@router.put("/{ip}/threshold/cpu", response_model=schemas.ThresholdResponse)
async def update_cpu_threshold_endpoint(
    ip: str,
    threshold_data: schemas.ThresholdUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=4.04, detail=f"Device with IP {ip} not found")

    device.cpu_threshold = threshold_data.threshold_value
    repo.db.commit()
    repo.db.refresh(device)

    return schemas.ThresholdResponse.model_validate(device)


@router.put("/{ip}/threshold/memory", response_model=schemas.ThresholdResponse)
async def update_memory_threshold_endpoint(
    ip: str,
    threshold_data: schemas.ThresholdUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=4.04, detail=f"Device with IP {ip} not found")

    device.memory_threshold = threshold_data.threshold_value
    repo.db.commit()
    repo.db.refresh(device)

    return schemas.ThresholdResponse.model_validate(device)


@router.put("/{ip}/threshold/reachability", response_model=schemas.ThresholdResponse)
async def update_reachability_threshold_endpoint(
    ip: str,
    threshold_data: schemas.FailureThresholdUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Update the failure threshold for device reachability.

    The failure threshold determines how many consecutive poll failures
    are required before a device is marked as unreachable.
    """
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    device.failure_threshold = threshold_data.threshold_value
    repo.db.commit()
    repo.db.refresh(device)

    return schemas.ThresholdResponse.model_validate(device)


@router.put("/{ip}/alert/cpu", response_model=schemas.AlertSentResponse)
async def update_cpu_alert_sent_endpoint(
    ip: str,
    alert_data: schemas.AlertSentUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=4.04, detail=f"Device with IP {ip} not found")

    device.cpu_alert_sent = alert_data.alert_sent
    repo.db.commit()
    repo.db.refresh(device)

    return schemas.AlertSentResponse.model_validate(device)


@router.put("/{ip}/alert/memory", response_model=schemas.AlertSentResponse)
async def update_memory_alert_sent_endpoint(
    ip: str,
    alert_data: schemas.AlertSentUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=4.04, detail=f"Device with IP {ip} not found")

    device.memory_alert_sent = alert_data.alert_sent
    repo.db.commit()
    repo.db.refresh(device)

    return schemas.AlertSentResponse.model_validate(device)

@router.put("/{ip}/interface/{if_index}/threshold", response_model=schemas.InterfaceThresholdResponse)
async def update_interface_threshold_endpoint(
    ip: str,
    if_index: int,
    threshold_data: schemas.ThresholdUpdate, # Reuse the same schema
    repo: DeviceRepository = Depends(get_repository)
):
    """
    Update the packet drop threshold for a specific interface.
    """
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()
    
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")

    interface.packet_drop_threshold = threshold_data.threshold_value
    repo.db.commit()
    repo.db.refresh(interface)

    return interface


# ==================== Phase 2: Alert State Management Endpoints ====================

@router.put("/{ip}/alert/cpu/acknowledge", response_model=schemas.AlertStateResponse)
async def acknowledge_cpu_alert(
    ip: str,
    data: schemas.AlertAcknowledge = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Acknowledge CPU alert to stop receiving notifications until recovery."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    if device.cpu_alert_state != "triggered":
        raise HTTPException(status_code=400, detail="No active CPU alert to acknowledge")

    device.cpu_alert_state = "acknowledged"
    device.cpu_acknowledged_at = datetime.now(timezone.utc)
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="CPU alert acknowledged",
        state=device.cpu_alert_state,
        acknowledged_at=device.cpu_acknowledged_at
    )


@router.put("/{ip}/alert/cpu/resolve", response_model=schemas.AlertStateResponse)
async def resolve_cpu_alert(
    ip: str,
    data: schemas.AlertResolve = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Manually resolve CPU alert (mark as false positive or resolved)."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    device.cpu_alert_state = "clear"
    device.cpu_acknowledged_at = None
    device.cpu_alert_sent = False  # Clear legacy flag
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="CPU alert resolved",
        state=device.cpu_alert_state,
        acknowledged_at=None
    )


@router.put("/{ip}/alert/memory/acknowledge", response_model=schemas.AlertStateResponse)
async def acknowledge_memory_alert(
    ip: str,
    data: schemas.AlertAcknowledge = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Acknowledge Memory alert to stop receiving notifications until recovery."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    if device.memory_alert_state != "triggered":
        raise HTTPException(status_code=400, detail="No active Memory alert to acknowledge")

    device.memory_alert_state = "acknowledged"
    device.memory_acknowledged_at = datetime.now(timezone.utc)
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="Memory alert acknowledged",
        state=device.memory_alert_state,
        acknowledged_at=device.memory_acknowledged_at
    )


@router.put("/{ip}/alert/memory/resolve", response_model=schemas.AlertStateResponse)
async def resolve_memory_alert(
    ip: str,
    data: schemas.AlertResolve = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Manually resolve Memory alert (mark as false positive or resolved)."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    device.memory_alert_state = "clear"
    device.memory_acknowledged_at = None
    device.memory_alert_sent = False  # Clear legacy flag
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="Memory alert resolved",
        state=device.memory_alert_state,
        acknowledged_at=None
    )


@router.put("/{ip}/alert/reachability/acknowledge", response_model=schemas.AlertStateResponse)
async def acknowledge_reachability_alert(
    ip: str,
    data: schemas.AlertAcknowledge = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Acknowledge Reachability alert to stop receiving notifications until recovery."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    if device.reachability_alert_state != "triggered":
        raise HTTPException(status_code=400, detail="No active Reachability alert to acknowledge")

    device.reachability_alert_state = "acknowledged"
    device.reachability_acknowledged_at = datetime.now(timezone.utc)
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="Reachability alert acknowledged",
        state=device.reachability_alert_state,
        acknowledged_at=device.reachability_acknowledged_at
    )


@router.put("/{ip}/alert/reachability/resolve", response_model=schemas.AlertStateResponse)
async def resolve_reachability_alert(
    ip: str,
    data: schemas.AlertResolve = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Manually resolve Reachability alert (mark as false positive or resolved)."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    device.reachability_alert_state = "clear"
    device.reachability_acknowledged_at = None
    device.reachability_alert_sent = False  # Clear legacy flag
    repo.db.commit()

    return schemas.AlertStateResponse(
        message="Reachability alert resolved",
        state=device.reachability_alert_state,
        acknowledged_at=None
    )


@router.put("/{ip}/interface/{if_index}/alert/status/acknowledge", response_model=schemas.AlertStateResponse)
async def acknowledge_interface_status_alert(
    ip: str,
    if_index: int,
    data: schemas.AlertAcknowledge = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Acknowledge interface operational status alert."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")

    if interface.oper_status_alert_state != "triggered":
        raise HTTPException(status_code=400, detail="No active interface status alert to acknowledge")

    interface.oper_status_alert_state = "acknowledged"
    interface.oper_status_acknowledged_at = datetime.now(timezone.utc)
    repo.db.commit()

    return schemas.AlertStateResponse(
        message=f"Interface {interface.if_name} status alert acknowledged",
        state=interface.oper_status_alert_state,
        acknowledged_at=interface.oper_status_acknowledged_at
    )


@router.put("/{ip}/interface/{if_index}/alert/status/resolve", response_model=schemas.AlertStateResponse)
async def resolve_interface_status_alert(
    ip: str,
    if_index: int,
    data: schemas.AlertResolve = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Manually resolve interface operational status alert."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")

    interface.oper_status_alert_state = "clear"
    interface.oper_status_acknowledged_at = None
    interface.oper_status_alert_sent = False  # Clear legacy flag
    repo.db.commit()

    return schemas.AlertStateResponse(
        message=f"Interface {interface.if_name} status alert resolved",
        state=interface.oper_status_alert_state,
        acknowledged_at=None
    )


@router.put("/{ip}/interface/{if_index}/alert/drops/acknowledge", response_model=schemas.AlertStateResponse)
async def acknowledge_interface_drops_alert(
    ip: str,
    if_index: int,
    data: schemas.AlertAcknowledge = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Acknowledge interface packet drop alert."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")

    if interface.packet_drop_alert_state != "triggered":
        raise HTTPException(status_code=400, detail="No active packet drop alert to acknowledge")

    interface.packet_drop_alert_state = "acknowledged"
    interface.packet_drop_acknowledged_at = datetime.now(timezone.utc)
    repo.db.commit()

    return schemas.AlertStateResponse(
        message=f"Interface {interface.if_name} packet drop alert acknowledged",
        state=interface.packet_drop_alert_state,
        acknowledged_at=interface.packet_drop_acknowledged_at
    )


@router.put("/{ip}/interface/{if_index}/alert/drops/resolve", response_model=schemas.AlertStateResponse)
async def resolve_interface_drops_alert(
    ip: str,
    if_index: int,
    data: schemas.AlertResolve = Body(default={}),
    repo: DeviceRepository = Depends(get_repository)
):
    """Manually resolve interface packet drop alert."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

    interface = repo.db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")

    interface.packet_drop_alert_state = "clear"
    interface.packet_drop_acknowledged_at = None
    interface.packet_drop_alert_sent = False  # Clear legacy flag
    repo.db.commit()

    return schemas.AlertStateResponse(
        message=f"Interface {interface.if_name} packet drop alert resolved",
        state=interface.packet_drop_alert_state,
        acknowledged_at=None
    )


@router.put("/{ip}/maintenance")
async def update_maintenance_mode(
    ip: str,
    data: schemas.MaintenanceModeUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """Enable or disable maintenance mode for a device to suppress all alerts."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with IP {ip} not found")

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