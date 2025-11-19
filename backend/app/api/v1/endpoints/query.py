from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func, select
from app.core import database, models, schemas
from app.core.exceptions import DeviceNotFoundError
from typing import List
import datetime

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)
get_db = database.get_db

def to_utc_iso(ts: datetime.datetime):
    """Force timestamp to UTC ISO8601 with Z suffix."""
    if ts is None:
        return None
    return ts.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")

@router.get("/network-summary", response_model=schemas.NetworkSummaryResponse)
async def get_network_summary(db: Session = Depends(get_db)):
    try:
        total_devices = db.query(models.Device).count()
        
        devices_in_alert = db.query(models.Device).filter(
            or_(
                models.Device.cpu_alert_state.in_(["triggered", "acknowledged"]),
                models.Device.memory_alert_state.in_(["triggered", "acknowledged"]),
                models.Device.reachability_alert_state.in_(["triggered", "acknowledged"])
            )
        ).count()
        
        interfaces_in_alert_q = db.query(models.Interface).filter(
            or_(
                models.Interface.packet_drop_alert_state.in_(["triggered", "acknowledged"]),
                models.Interface.oper_status_alert_state.in_(["triggered", "acknowledged"])
            )
        )
        
        devices_with_if_alert = interfaces_in_alert_q.distinct(models.Interface.device_id)\
            .join(models.Device)\
            .filter(
                models.Device.cpu_alert_state == "clear",
                models.Device.memory_alert_state == "clear",
                models.Device.reachability_alert_state == "clear"
            ).count()

        total_alerts = devices_in_alert + devices_with_if_alert

        # Count devices that are reachable (online)
        devices_up = db.query(models.Device).filter(
            models.Device.is_reachable == True
        ).count()

        return schemas.NetworkSummaryResponse(
            total_devices=total_devices,
            devices_in_alert=total_alerts,
            devices_up=devices_up
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting network summary: {str(e)}")


# -------------------------------
#  FIXED: /device/{ip}/metrics
# -------------------------------
@router.get("/device/{ip}/metrics", response_model=List[schemas.DeviceMetricResponse])
async def get_device_metrics_history(
    ip: str, 
    db: Session = Depends(get_db),
    limit: int = 15
):
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise DeviceNotFoundError(ip)

    metrics = db.query(models.DeviceMetric)\
                .filter(models.DeviceMetric.device_id == device.id)\
                .order_by(models.DeviceMetric.timestamp.desc())\
                .limit(limit)\
                .all()

    # Force timestamps to UTC ISO8601
    for m in metrics:
        m.timestamp = to_utc_iso(m.timestamp)

    return metrics


# -------------------------------
#  FIXED: /device/{ip}/interfaces
# -------------------------------
@router.get("/device/{ip}/interfaces", response_model=List[schemas.InterfaceMetricResponse])
async def get_device_interface_latest(
    ip: str, 
    db: Session = Depends(get_db)
):
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise DeviceNotFoundError(ip)

    try:
        subq = db.query(
            models.InterfaceMetric.interface_id,
            func.max(models.InterfaceMetric.timestamp).label("max_timestamp")
        ).join(models.Interface).filter(models.Interface.device_id == device.id)\
         .group_by(models.InterfaceMetric.interface_id).subquery()

        results = db.query(
            models.InterfaceMetric,
            models.Interface.if_name,
            models.Interface.if_index,
            models.Interface.packet_drop_threshold
        ).join(subq, (models.InterfaceMetric.interface_id == subq.c.interface_id) & \
                     (models.InterfaceMetric.timestamp == subq.c.max_timestamp))\
         .join(models.Interface, models.InterfaceMetric.interface_id == models.Interface.id)\
         .all()

        latest_metrics = []
        for metric, if_name, if_index, packet_drop_threshold in results:

            # Convert timestamp
            metric.timestamp = to_utc_iso(metric.timestamp)

            metric_data = schemas.InterfaceMetricResponse.model_validate(metric)
            metric_data.if_name = if_name
            metric_data.if_index = if_index
            metric_data.packet_drop_threshold = packet_drop_threshold
            latest_metrics.append(metric_data)

        return latest_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting interface metrics: {str(e)}")


@router.get("/top-devices", response_model=List[schemas.TopDeviceResponse])
async def get_top_devices(
    metric: str = Query(..., enum=["cpu", "memory"]), 
    db: Session = Depends(get_db)
):
    if metric not in ["cpu", "memory"]:
        raise HTTPException(status_code=400, detail="Metric must be 'cpu' or 'memory'")
    
    try:
        subq = db.query(
            func.max(models.DeviceMetric.id).label("max_id")
        ).group_by(models.DeviceMetric.device_id).subquery()

        query = db.query(
            models.DeviceMetric, 
            models.Device.hostname, 
            models.Device.ip_address
        ).join(subq, models.DeviceMetric.id == subq.c.max_id)\
         .join(models.Device, models.Device.id == models.DeviceMetric.device_id)

        if metric == "cpu":
            query = query.order_by(models.DeviceMetric.cpu_utilization.desc())
        else:
            query = query.order_by(models.DeviceMetric.memory_utilization.desc())
            
        top_5 = query.limit(5).all()

        response = []
        for metric_data, hostname, ip_address in top_5:
            response.append(schemas.TopDeviceResponse(
                hostname=hostname,
                ip_address=ip_address,
                value=metric_data.cpu_utilization if metric == "cpu" else metric_data.memory_utilization
            ))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting top devices: {str(e)}")


# -------------------------------
#  FIXED: /history/device
# -------------------------------
@router.post("/history/device", response_model=List[schemas.DeviceMetricResponse])
async def get_history_for_report(
    query: schemas.HistoryQuery,
    db: Session = Depends(get_db)
):
    device = db.query(models.Device).filter(models.Device.ip_address == query.ip_address).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    metrics = db.query(models.DeviceMetric)\
                .filter(models.DeviceMetric.device_id == device.id)\
                .filter(
                    models.DeviceMetric.timestamp >= query.start_time,
                    models.DeviceMetric.timestamp <= query.end_time
                )\
                .order_by(models.DeviceMetric.timestamp.asc())\
                .limit(15)\
                .all()

    for m in metrics:
        m.timestamp = to_utc_iso(m.timestamp)

    return metrics


# -------------------------------
#  FIXED: /network-throughput
# -------------------------------
@router.get("/network-throughput", response_model=List[schemas.ThroughputDatapoint])
async def get_network_throughput(
    db: Session = Depends(get_db),
    limit: int = 100
):
    lag_subquery = select(
        models.InterfaceMetric.timestamp,
        models.InterfaceMetric.octets_in,
        models.InterfaceMetric.octets_out,
        func.lag(models.InterfaceMetric.octets_in, 1, 0).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_octets_in"),
        func.lag(models.InterfaceMetric.octets_out, 1, 0).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_octets_out"),
        func.lag(models.InterfaceMetric.timestamp, 1, None).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_timestamp")
    ).subquery()

    delta_subquery = select(
        lag_subquery.c.timestamp,
        (lag_subquery.c.octets_in - lag_subquery.c.prev_octets_in).label("delta_in"),
        (lag_subquery.c.octets_out - lag_subquery.c.prev_octets_out).label("delta_out"),
        func.extract("epoch", lag_subquery.c.timestamp - lag_subquery.c.prev_timestamp).label("delta_seconds")
    ).filter(lag_subquery.c.prev_timestamp != None).subquery()

    results = db.query(
        delta_subquery.c.timestamp,
        (func.sum(delta_subquery.c.delta_in) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("inbound_bps"),
        (func.sum(delta_subquery.c.delta_out) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("outbound_bps")
    ).group_by(delta_subquery.c.timestamp)\
     .order_by(delta_subquery.c.timestamp.desc())\
     .limit(limit)\
     .all()

    output = []
    for ts, bps_in, bps_out in reversed(results):
        output.append(
            schemas.ThroughputDatapoint(
                timestamp=to_utc_iso(ts),
                inbound_bps=bps_in if bps_in and bps_in > 0 else 0,
                outbound_bps=bps_out if bps_out and bps_out > 0 else 0
            )
        )

    return output


@router.get("/alerts/active", response_model=List[schemas.ActiveAlertResponse])
async def get_active_alerts(db: Session = Depends(get_db)):
    """
    Retrieve all active alerts from the system.
    """
    all_alerts: List[schemas.ActiveAlertResponse] = []

    # --- 1. Get Latest Device Metric IDs ---
    # (Uses the same subquery logic as your /top-devices endpoint)
    latest_device_metrics_subq = db.query(
        func.max(models.DeviceMetric.id).label("max_id")
    ).group_by(models.DeviceMetric.device_id).subquery()

    # --- 2. Query for CPU & Memory Alerts ---
    device_alerts_query = db.query(
        models.Device,
        models.DeviceMetric.cpu_utilization,
        models.DeviceMetric.memory_utilization
    ).join(
        models.DeviceMetric,
        models.Device.id == models.DeviceMetric.device_id
    ).join(
        latest_device_metrics_subq,
        models.DeviceMetric.id == latest_device_metrics_subq.c.max_id
    ).filter(
        or_(
            models.Device.cpu_alert_state.in_(["triggered", "acknowledged"]),
            models.Device.memory_alert_state.in_(["triggered", "acknowledged"])
        )
    ).all()

    for device, cpu, mem in device_alerts_query:
        if device.cpu_alert_state in ["triggered", "acknowledged"]:
            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=device.hostname,
                ip_address=device.ip_address,
                metric="High CPU",
                current_value=f"{cpu:.2f}%",
                threshold=f">{device.cpu_threshold}%",
                state=device.cpu_alert_state,
                acknowledged_at=device.cpu_acknowledged_at
            ))
        if device.memory_alert_state in ["triggered", "acknowledged"]:
            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=device.hostname,
                ip_address=device.ip_address,
                metric="High Memory",
                current_value=f"{mem:.2f}%",
                threshold=f">{device.memory_threshold}%",
                state=device.memory_alert_state,
                acknowledged_at=device.memory_acknowledged_at
            ))

    # --- 3. Query for Reachability Alerts ---
    reachability_alerts_query = db.query(models.Device).filter(
        models.Device.reachability_alert_state.in_(["triggered", "acknowledged"])
    ).all()

    for device in reachability_alerts_query:
        all_alerts.append(schemas.ActiveAlertResponse(
            hostname=device.hostname,
            ip_address=device.ip_address,
            metric="Device Unreachable",
            current_value=f"Down ({device.consecutive_failures} failures)",
            threshold=f">{device.failure_threshold} failures",
            state=device.reachability_alert_state,
            acknowledged_at=device.reachability_acknowledged_at
        ))

    # --- 5. Get Latest Interface Metric Timestamps ---
    # (Uses the same subquery logic as your /device/{ip}/interfaces endpoint)
    latest_interface_metrics_subq = db.query(
        models.InterfaceMetric.interface_id,
        func.max(models.InterfaceMetric.timestamp).label("max_timestamp")
    ).group_by(models.InterfaceMetric.interface_id).subquery()

    # --- 6. Query for Interface Alerts ---
    interface_alerts_query = db.query(
        models.Interface,
        models.Device.hostname,
        models.Device.ip_address,
        models.InterfaceMetric.oper_status,
        models.InterfaceMetric.discards_in,
        models.InterfaceMetric.discards_out
    ).join(
        latest_interface_metrics_subq,
        models.Interface.id == latest_interface_metrics_subq.c.interface_id
    ).join(
        models.InterfaceMetric,
        (models.InterfaceMetric.interface_id == latest_interface_metrics_subq.c.interface_id) &
        (models.InterfaceMetric.timestamp == latest_interface_metrics_subq.c.max_timestamp)
    ).join(
        models.Device,
        models.Interface.device_id == models.Device.id
    ).filter(
        or_(
            models.Interface.oper_status_alert_state.in_(["triggered", "acknowledged"]),
            models.Interface.packet_drop_alert_state.in_(["triggered", "acknowledged"])
        )
    ).all()

    for interface, hostname, ip, status, disc_in, disc_out in interface_alerts_query:
        if interface.oper_status_alert_state in ["triggered", "acknowledged"]:
            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=hostname,
                ip_address=ip,
                metric=f"Interface Down ({interface.if_name})",
                current_value="Down" if status != 1 else "Up", # status 1=up
                threshold="Should be Up",
                state=interface.oper_status_alert_state,
                acknowledged_at=interface.oper_status_acknowledged_at,
                if_index=interface.if_index
            ))
        if interface.packet_drop_alert_state in ["triggered", "acknowledged"]:
            total_drops = (disc_in or 0) + (disc_out or 0)
            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=hostname,
                ip_address=ip,
                metric=f"Packet Drops ({interface.if_name})",
                current_value=f"{total_drops} drops",
                threshold=f">{interface.packet_drop_threshold} drops",
                state=interface.packet_drop_alert_state,
                acknowledged_at=interface.packet_drop_acknowledged_at,
                if_index=interface.if_index
            ))

    return all_alerts
