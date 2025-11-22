from datetime import datetime, timezone
from fastapi import Depends, APIRouter, HTTPException
from app.core import database, models, schemas
from app.core.exceptions import DeviceNotFoundError, InterfaceNotFoundError, AlertNotFoundError
from app.core.security import get_current_user
from services import device_service
from services.device_service import DeviceRepository, get_repository

router = APIRouter(
    prefix="/device",
    tags=["Device Alerts"],
    dependencies=[Depends(get_current_user)]  # Require authentication
)


# ==================== Device Alert Management ====================

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


# ==================== Interface Alert Management ====================

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
