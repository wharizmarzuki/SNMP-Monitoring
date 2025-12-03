from datetime import datetime, timedelta, timezone
from fastapi import Depends, APIRouter
from app.core import database, models, schemas
from app.core.exceptions import DeviceNotFoundError, InterfaceNotFoundError
from app.core.cache import cache
from app.core.security import get_current_user
from services import device_service
from services.device_service import DeviceRepository, get_repository

router = APIRouter(
    prefix="/device",
    tags=["Device Configuration"],
    dependencies=[Depends(get_current_user)]
)


@router.put("/{ip}/thresholds", response_model=schemas.DeviceResponse)
async def update_device_thresholds_batch(
    ip: str,
    thresholds: schemas.ThresholdBatchUpdate,
    repo: DeviceRepository = Depends(get_repository)
):
    """Batch update device thresholds. Only provided thresholds will be updated."""
    device = device_service.get_device_by_ip(ip, repo)
    if not device:
        raise DeviceNotFoundError(ip)

    if thresholds.cpu_threshold is not None:
        device.cpu_threshold = thresholds.cpu_threshold
    if thresholds.memory_threshold is not None:
        device.memory_threshold = thresholds.memory_threshold
    if thresholds.failure_threshold is not None:
        device.failure_threshold = thresholds.failure_threshold

    repo.db.commit()
    repo.db.refresh(device)

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
