"""
Alert history query endpoints.
Provides access to historical alert data with filtering and pagination.
"""
from datetime import datetime
from typing import Optional
from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.core import database, models, schemas
from app.core.security import get_current_user

router = APIRouter(
    prefix="/alerts",
    tags=["Alert History"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/history", response_model=list[schemas.AlertHistoryResponse])
async def get_alert_history(
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    interface_id: Optional[int] = Query(None, description="Filter by interface ID"),
    start_time: Optional[datetime] = Query(None, description="Filter alerts after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter alerts before this time"),
    include_cleared: bool = Query(True, description="Include cleared alerts"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(database.get_db)
):
    """
    Get paginated alert history with optional filters.

    Query parameters:
    - alert_type: cpu, memory, reachability, interface_status, packet_drop
    - severity: Warning, High, Critical
    - device_id: Filter by specific device
    - interface_id: Filter by specific interface
    - start_time: ISO 8601 timestamp
    - end_time: ISO 8601 timestamp
    - include_cleared: Whether to include cleared alerts (default: true)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 500)
    """
    query = db.query(models.AlertHistory)

    # Apply filters
    if alert_type:
        query = query.filter(models.AlertHistory.alert_type == alert_type)
    if severity:
        query = query.filter(models.AlertHistory.severity == severity)
    if device_id:
        query = query.filter(models.AlertHistory.device_id == device_id)
    if interface_id:
        query = query.filter(models.AlertHistory.interface_id == interface_id)
    if start_time:
        query = query.filter(models.AlertHistory.triggered_at >= start_time)
    if end_time:
        query = query.filter(models.AlertHistory.triggered_at <= end_time)
    if not include_cleared:
        query = query.filter(models.AlertHistory.cleared_at.is_(None))

    # Order by most recent first
    query = query.order_by(desc(models.AlertHistory.triggered_at))

    # Pagination
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    return results


@router.get("/history/{alert_id}", response_model=schemas.AlertHistoryDetailResponse)
async def get_alert_history_detail(
    alert_id: int,
    db: Session = Depends(database.get_db)
):
    """Get detailed information for a specific alert history record."""
    alert = db.query(models.AlertHistory).filter(
        models.AlertHistory.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert history record not found")

    return alert


@router.get("/history/device/{ip}", response_model=list[schemas.AlertHistoryResponse])
async def get_device_alert_history(
    ip: str,
    alert_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    include_cleared: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(database.get_db)
):
    """Get alert history for a specific device by IP address."""
    # Find device
    device = db.query(models.Device).filter(
        models.Device.ip_address == ip
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device {ip} not found")

    # Query alert history
    query = db.query(models.AlertHistory).filter(
        models.AlertHistory.device_id == device.id
    )

    if alert_type:
        query = query.filter(models.AlertHistory.alert_type == alert_type)
    if start_time:
        query = query.filter(models.AlertHistory.triggered_at >= start_time)
    if end_time:
        query = query.filter(models.AlertHistory.triggered_at <= end_time)
    if not include_cleared:
        query = query.filter(models.AlertHistory.cleared_at.is_(None))

    query = query.order_by(desc(models.AlertHistory.triggered_at))
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    return results


@router.get("/history/device/{ip}/interfaces/{if_index}", response_model=list[schemas.AlertHistoryResponse])
async def get_interface_alert_history(
    ip: str,
    if_index: int,
    alert_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    include_cleared: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(database.get_db)
):
    """Get alert history for a specific interface."""
    # Find device and interface
    device = db.query(models.Device).filter(
        models.Device.ip_address == ip
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device {ip} not found")

    interface = db.query(models.Interface).filter(
        models.Interface.device_id == device.id,
        models.Interface.if_index == if_index
    ).first()

    if not interface:
        raise HTTPException(status_code=404, detail=f"Interface {if_index} not found on device {ip}")

    # Query alert history
    query = db.query(models.AlertHistory).filter(
        models.AlertHistory.interface_id == interface.id
    )

    if alert_type:
        query = query.filter(models.AlertHistory.alert_type == alert_type)
    if start_time:
        query = query.filter(models.AlertHistory.triggered_at >= start_time)
    if end_time:
        query = query.filter(models.AlertHistory.triggered_at <= end_time)
    if not include_cleared:
        query = query.filter(models.AlertHistory.cleared_at.is_(None))

    query = query.order_by(desc(models.AlertHistory.triggered_at))
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    return results


@router.get("/history/stats", response_model=schemas.AlertHistoryStatsResponse)
async def get_alert_history_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(database.get_db)
):
    """Get alert history statistics."""
    query = db.query(models.AlertHistory)

    if start_time:
        query = query.filter(models.AlertHistory.triggered_at >= start_time)
    if end_time:
        query = query.filter(models.AlertHistory.triggered_at <= end_time)

    total_alerts = query.count()
    active_alerts = query.filter(models.AlertHistory.cleared_at.is_(None)).count()
    cleared_alerts = total_alerts - active_alerts

    # Count by severity
    critical_count = query.filter(models.AlertHistory.severity == "Critical").count()
    high_count = query.filter(models.AlertHistory.severity == "High").count()
    warning_count = query.filter(models.AlertHistory.severity == "Warning").count()

    # Email stats
    email_sent_count = query.filter(models.AlertHistory.email_sent == True).count()
    email_failed_count = query.filter(models.AlertHistory.email_status == "failed").count()

    return schemas.AlertHistoryStatsResponse(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        cleared_alerts=cleared_alerts,
        critical_count=critical_count,
        high_count=high_count,
        warning_count=warning_count,
        email_sent_count=email_sent_count,
        email_failed_count=email_failed_count
    )
