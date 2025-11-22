from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func, select, and_, case
from app.core import database, models, schemas
from app.core.exceptions import DeviceNotFoundError
from app.core.cache import cache
from app.core.security import get_current_user
from typing import List
import datetime

router = APIRouter(
    prefix="/query",
    tags=["Query"],
    dependencies=[Depends(get_current_user)]  # Require authentication for all query endpoints
)
get_db = database.get_db

def to_utc_iso(ts: datetime.datetime):
    """Force timestamp to UTC ISO8601 with Z suffix."""
    if ts is None:
        return None
    return ts.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")

@router.get("/network-summary", response_model=schemas.NetworkSummaryResponse)
async def get_network_summary(db: Session = Depends(get_db)):
    """Get network summary with 30-second cache"""
    cache_key = "network_summary"

    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return schemas.NetworkSummaryResponse(**cached_data)

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

        # Count devices that are down
        devices_down = db.query(models.Device).filter(
            models.Device.is_reachable == False
        ).count()

        result = {
            "total_devices": total_devices,
            "devices_in_alert": total_alerts,
            "devices_up": devices_up,
            "devices_down": devices_down
        }

        # Cache for 30 seconds
        cache.set(cache_key, result, ttl=30)

        return schemas.NetworkSummaryResponse(**result)
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
@router.get("/device/{ip}/interfaces/summary", response_model=List[schemas.InterfaceSummaryResponse])
async def get_device_interface_summary(
    ip: str,
    db: Session = Depends(get_db)
):
    """
    Get optimized interface summary (only essential fields).
    Reduces payload size by 60-80% compared to full interface metrics.
    """
    device = db.query(models.Device).filter(models.Device.ip_address == ip).first()
    if not device:
        raise DeviceNotFoundError(ip)

    try:
        # Get latest metrics for each interface
        subquery = (
            db.query(
                models.InterfaceMetric.interface_id,
                func.max(models.InterfaceMetric.timestamp).label('max_timestamp')
            )
            .join(models.Interface)
            .filter(models.Interface.device_id == device.id)
            .group_by(models.InterfaceMetric.interface_id)
            .subquery()
        )

        # Query only essential fields
        interfaces = (
            db.query(
                models.Interface.if_index,
                models.Interface.if_name,
                models.Interface.packet_drop_threshold,
                models.InterfaceMetric.oper_status,
                models.InterfaceMetric.admin_status,
                models.InterfaceMetric.octets_in,
                models.InterfaceMetric.octets_out,
                models.InterfaceMetric.discards_in,
                models.InterfaceMetric.discards_out,
                models.InterfaceMetric.errors_in,
                models.InterfaceMetric.errors_out
            )
            .join(
                models.InterfaceMetric,
                models.InterfaceMetric.interface_id == models.Interface.id
            )
            .join(
                subquery,
                and_(
                    models.InterfaceMetric.interface_id == subquery.c.interface_id,
                    models.InterfaceMetric.timestamp == subquery.c.max_timestamp
                )
            )
            .filter(models.Interface.device_id == device.id)
            .all()
        )

        # Build response with only essential fields
        return [schemas.InterfaceSummaryResponse(
            if_index=intf[0],
            if_name=intf[1],
            if_descr=None,  # Not stored in current model
            oper_status=intf[3],
            admin_status=intf[4],
            octets_in=int(intf[5]) if intf[5] is not None else None,
            octets_out=int(intf[6]) if intf[6] is not None else None,
            discards_in=int(intf[7]) if intf[7] is not None else None,
            discards_out=int(intf[8]) if intf[8] is not None else None,
            errors_in=int(intf[9]) if intf[9] is not None else None,
            errors_out=int(intf[10]) if intf[10] is not None else None,
            packet_drop_threshold=intf[2]
        ) for intf in interfaces]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting interface summary: {str(e)}")


@router.get("/top-devices", response_model=List[schemas.TopDeviceResponse])
async def get_top_devices(
    metric: str = Query(..., enum=["cpu", "memory"]),
    db: Session = Depends(get_db)
):
    """Get top devices with 60-second cache"""
    if metric not in ["cpu", "memory"]:
        raise HTTPException(status_code=400, detail="Metric must be 'cpu' or 'memory'")

    cache_key = f"top_devices:{metric}"

    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return [schemas.TopDeviceResponse(**d) for d in cached_data]

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

        result = []
        for metric_data, hostname, ip_address in top_5:
            result.append({
                "hostname": hostname,
                "ip_address": ip_address,
                "value": metric_data.cpu_utilization if metric == "cpu" else metric_data.memory_utilization
            })

        # Cache for 60 seconds
        cache.set(cache_key, result, ttl=60)

        return [schemas.TopDeviceResponse(**d) for d in result]
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

    # Counter wrap detection: Counter32 max value is 2^32 = 4,294,967,296
    # If current < previous, counter wrapped: delta = (2^32 - previous) + current
    # Otherwise: delta = current - previous
    COUNTER32_MAX = 2 ** 32

    delta_in_expr = case(
        (lag_subquery.c.octets_in >= lag_subquery.c.prev_octets_in,
         lag_subquery.c.octets_in - lag_subquery.c.prev_octets_in),
        else_=(COUNTER32_MAX - lag_subquery.c.prev_octets_in + lag_subquery.c.octets_in)
    ).label("delta_in")

    delta_out_expr = case(
        (lag_subquery.c.octets_out >= lag_subquery.c.prev_octets_out,
         lag_subquery.c.octets_out - lag_subquery.c.prev_octets_out),
        else_=(COUNTER32_MAX - lag_subquery.c.prev_octets_out + lag_subquery.c.octets_out)
    ).label("delta_out")

    delta_subquery = select(
        lag_subquery.c.timestamp,
        delta_in_expr,
        delta_out_expr,
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


@router.get("/device-utilization", response_model=List[schemas.DeviceUtilizationDatapoint])
async def get_device_utilization(
    db: Session = Depends(get_db),
    minutes: int = 60,  # Time range in minutes (default 1 hour)
    interval_minutes: int = 1  # Aggregation interval in minutes (default 1 minute)
):
    """
    Get per-device throughput and utilization metrics over time (time series).

    Returns time series data for devices showing:
    - Throughput (bps) over time
    - Total capacity (sum of interface speeds)
    - Utilization percentages over time

    Parameters:
    - minutes: Time range to fetch data for (e.g., 15, 30, 60)
    - interval_minutes: Data aggregation interval (e.g., 1, 5, 10)

    Only includes devices with at least one interface that has known speed.
    Data points are ordered chronologically for time series visualization.
    """
    from datetime import datetime, timedelta

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes)

    # Join interface_metrics with interfaces to get speed_bps and device_id
    lag_subquery = select(
        models.Interface.device_id,
        models.Interface.speed_bps,
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
    ).join(
        models.Interface,
        models.InterfaceMetric.interface_id == models.Interface.id
    ).filter(
        models.Interface.speed_bps != None,  # Only include interfaces with known speed
        models.InterfaceMetric.timestamp >= start_time,
        models.InterfaceMetric.timestamp <= end_time
    ).subquery()

    # Counter wrap detection
    COUNTER32_MAX = 2 ** 32

    delta_in_expr = case(
        (lag_subquery.c.octets_in >= lag_subquery.c.prev_octets_in,
         lag_subquery.c.octets_in - lag_subquery.c.prev_octets_in),
        else_=(COUNTER32_MAX - lag_subquery.c.prev_octets_in + lag_subquery.c.octets_in)
    ).label("delta_in")

    delta_out_expr = case(
        (lag_subquery.c.octets_out >= lag_subquery.c.prev_octets_out,
         lag_subquery.c.octets_out - lag_subquery.c.prev_octets_out),
        else_=(COUNTER32_MAX - lag_subquery.c.prev_octets_out + lag_subquery.c.octets_out)
    ).label("delta_out")

    delta_subquery = select(
        lag_subquery.c.device_id,
        lag_subquery.c.speed_bps,
        lag_subquery.c.timestamp,
        delta_in_expr,
        delta_out_expr,
        func.extract("epoch", lag_subquery.c.timestamp - lag_subquery.c.prev_timestamp).label("delta_seconds")
    ).filter(lag_subquery.c.prev_timestamp != None).subquery()

    # Aggregate by device and time interval
    device_aggregation = select(
        delta_subquery.c.device_id,
        delta_subquery.c.timestamp,
        (func.sum(delta_subquery.c.delta_in) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("inbound_bps"),
        (func.sum(delta_subquery.c.delta_out) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("outbound_bps"),
        func.sum(delta_subquery.c.speed_bps).label("total_capacity_bps")
    ).group_by(
        delta_subquery.c.device_id,
        delta_subquery.c.timestamp
    ).subquery()

    # Join with devices table to get hostname and ip_address
    # Return time series data (multiple timestamps per device)
    final_query = select(
        models.Device.id.label("device_id"),
        models.Device.hostname,
        models.Device.ip_address,
        device_aggregation.c.timestamp,
        device_aggregation.c.inbound_bps,
        device_aggregation.c.outbound_bps,
        device_aggregation.c.total_capacity_bps
    ).join(
        device_aggregation,
        models.Device.id == device_aggregation.c.device_id
    ).order_by(
        device_aggregation.c.timestamp.asc()
    )

    results = db.execute(final_query).all()

    output = []
    # Process results and optionally sample by interval
    results_list = list(results)

    # If interval_minutes > 1, sample the data
    if interval_minutes > 1 and len(results_list) > 0:
        # Group by device and sample
        from collections import defaultdict
        device_groups = defaultdict(list)

        for row in results_list:
            device_groups[row.device_id].append(row)

        sampled_results = []
        for device_id, rows in device_groups.items():
            # Sample every Nth row based on interval_minutes
            for i in range(0, len(rows), interval_minutes):
                sampled_results.append(rows[i])

        results_list = sorted(sampled_results, key=lambda x: x.timestamp)

    for row in results_list:
        # Calculate utilization percentages
        utilization_in_pct = None
        utilization_out_pct = None
        max_utilization_pct = None

        if row.total_capacity_bps and row.total_capacity_bps > 0:
            utilization_in_pct = (row.inbound_bps / row.total_capacity_bps) * 100
            utilization_out_pct = (row.outbound_bps / row.total_capacity_bps) * 100
            max_utilization_pct = max(utilization_in_pct, utilization_out_pct)

        output.append(
            schemas.DeviceUtilizationDatapoint(
                device_id=row.device_id,
                hostname=row.hostname,
                ip_address=row.ip_address,
                timestamp=to_utc_iso(row.timestamp),
                inbound_bps=row.inbound_bps if row.inbound_bps and row.inbound_bps > 0 else 0,
                outbound_bps=row.outbound_bps if row.outbound_bps and row.outbound_bps > 0 else 0,
                total_capacity_bps=row.total_capacity_bps,
                utilization_in_pct=utilization_in_pct,
                utilization_out_pct=utilization_out_pct,
                max_utilization_pct=max_utilization_pct
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
            # Calculate severity based on CPU utilization
            cpu_severity = "Warning"
            if cpu >= 90:
                cpu_severity = "Critical"
            elif cpu >= 75:
                cpu_severity = "High"

            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=device.hostname,
                ip_address=device.ip_address,
                metric="High CPU",
                current_value=f"{cpu:.2f}%",
                threshold=f">{device.cpu_threshold}%",
                state=device.cpu_alert_state,
                acknowledged_at=device.cpu_acknowledged_at,
                severity=cpu_severity
            ))
        if device.memory_alert_state in ["triggered", "acknowledged"]:
            # Calculate severity based on Memory utilization
            mem_severity = "Warning"
            if mem >= 90:
                mem_severity = "Critical"
            elif mem >= 75:
                mem_severity = "High"

            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=device.hostname,
                ip_address=device.ip_address,
                metric="High Memory",
                current_value=f"{mem:.2f}%",
                threshold=f">{device.memory_threshold}%",
                state=device.memory_alert_state,
                acknowledged_at=device.memory_acknowledged_at,
                severity=mem_severity
            ))

    # --- 3. Query for Reachability Alerts ---
    reachability_alerts_query = db.query(models.Device).filter(
        models.Device.reachability_alert_state.in_(["triggered", "acknowledged"])
    ).all()

    for device in reachability_alerts_query:
        # Reachability alerts are always Critical
        all_alerts.append(schemas.ActiveAlertResponse(
            hostname=device.hostname,
            ip_address=device.ip_address,
            metric="Device Unreachable",
            current_value=f"Down ({device.consecutive_failures} failures)",
            threshold=f">{device.failure_threshold} failures",
            state=device.reachability_alert_state,
            acknowledged_at=device.reachability_acknowledged_at,
            severity="Critical"
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
            # Interface down alerts are High severity
            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=hostname,
                ip_address=ip,
                metric=f"Interface Down ({interface.if_name})",
                current_value="Down" if status != 1 else "Up", # status 1=up
                threshold="Should be Up",
                state=interface.oper_status_alert_state,
                acknowledged_at=interface.oper_status_acknowledged_at,
                if_index=interface.if_index,
                severity="High"
            ))
        if interface.packet_drop_alert_state in ["triggered", "acknowledged"]:
            total_drops = (disc_in or 0) + (disc_out or 0)
            # Packet drop severity based on total drops
            drop_severity = "Warning"
            if total_drops >= 10000:
                drop_severity = "Critical"
            elif total_drops >= 1000:
                drop_severity = "High"

            all_alerts.append(schemas.ActiveAlertResponse(
                hostname=hostname,
                ip_address=ip,
                metric=f"Packet Drops ({interface.if_name})",
                current_value=f"{total_drops} drops",
                threshold=f">{interface.packet_drop_threshold} drops",
                state=interface.packet_drop_alert_state,
                acknowledged_at=interface.packet_drop_acknowledged_at,
                if_index=interface.if_index,
                severity=drop_severity
            ))

    return all_alerts


# -------------------------------
#  REPORT ENDPOINTS
# -------------------------------

@router.get("/report/network-throughput", response_model=List[schemas.NetworkThroughputDatapoint])
async def get_report_network_throughput(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Get network-wide throughput aggregated across all interfaces for report date range.
    Returns time series of total inbound/outbound bandwidth.
    """
    # Convert string dates to datetime (will be in format YYYY-MM-DDTHH:MM:SS)
    start_dt = datetime.datetime.fromisoformat(start_date)
    end_dt = datetime.datetime.fromisoformat(end_date)

    # Use LAG window function to calculate deltas (same logic as existing /query/network-throughput)
    lag_subquery = select(
        models.InterfaceMetric.interface_id,
        models.InterfaceMetric.timestamp,
        models.InterfaceMetric.octets_in,
        models.InterfaceMetric.octets_out,
        func.lag(models.InterfaceMetric.octets_in).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_in"),
        func.lag(models.InterfaceMetric.octets_out).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_out"),
        func.lag(models.InterfaceMetric.timestamp).over(
            partition_by=models.InterfaceMetric.interface_id,
            order_by=models.InterfaceMetric.timestamp
        ).label("prev_timestamp")
    ).filter(
        models.InterfaceMetric.timestamp >= start_dt,
        models.InterfaceMetric.timestamp <= end_dt
    ).subquery()

    # Calculate deltas with counter wrap detection
    delta_subquery = select(
        lag_subquery.c.interface_id,
        lag_subquery.c.timestamp,
        case(
            (lag_subquery.c.octets_in >= lag_subquery.c.prev_in,
             lag_subquery.c.octets_in - lag_subquery.c.prev_in),
            else_=(2**32 + lag_subquery.c.octets_in - lag_subquery.c.prev_in)
        ).label("delta_in"),
        case(
            (lag_subquery.c.octets_out >= lag_subquery.c.prev_out,
             lag_subquery.c.octets_out - lag_subquery.c.prev_out),
            else_=(2**32 + lag_subquery.c.octets_out - lag_subquery.c.prev_out)
        ).label("delta_out"),
        func.extract("epoch", lag_subquery.c.timestamp - lag_subquery.c.prev_timestamp).label("delta_seconds")
    ).filter(lag_subquery.c.prev_timestamp != None).subquery()

    # Aggregate throughput across all interfaces per timestamp
    results = db.query(
        delta_subquery.c.timestamp,
        (func.sum(delta_subquery.c.delta_in) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("inbound_bps"),
        (func.sum(delta_subquery.c.delta_out) * 8 / func.avg(delta_subquery.c.delta_seconds)).label("outbound_bps")
    ).group_by(delta_subquery.c.timestamp)\
     .order_by(delta_subquery.c.timestamp.asc())\
     .all()

    output = []
    for ts, bps_in, bps_out in results:
        output.append(schemas.NetworkThroughputDatapoint(
            timestamp=to_utc_iso(ts),
            total_inbound_bps=bps_in if bps_in and bps_in > 0 else 0.0,
            total_outbound_bps=bps_out if bps_out and bps_out > 0 else 0.0
        ))

    return output


@router.get("/report/device-utilization", response_model=List[schemas.ReportDeviceUtilizationDatapoint])
async def get_report_device_utilization(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Get network-wide CPU/Memory utilization metrics for report date range.
    Returns time series of average and max utilization across all devices.
    """
    start_dt = datetime.datetime.fromisoformat(start_date)
    end_dt = datetime.datetime.fromisoformat(end_date)

    # Query to get CPU/Memory stats grouped by timestamp
    utilization_data = db.query(
        models.DeviceMetric.timestamp,
        func.avg(models.DeviceMetric.cpu_utilization).label('avg_cpu'),
        func.avg(models.DeviceMetric.memory_utilization).label('avg_memory'),
        func.max(models.DeviceMetric.cpu_utilization).label('max_cpu'),
        func.max(models.DeviceMetric.memory_utilization).label('max_memory'),
        func.count(func.distinct(models.DeviceMetric.device_id)).label('devices_sampled')
    ).filter(
        models.DeviceMetric.timestamp >= start_dt,
        models.DeviceMetric.timestamp <= end_dt
    ).group_by(
        models.DeviceMetric.timestamp
    ).order_by(
        models.DeviceMetric.timestamp.asc()
    ).all()

    results = []
    for row in utilization_data:
        results.append(schemas.ReportDeviceUtilizationDatapoint(
            timestamp=to_utc_iso(row.timestamp),
            avg_cpu_utilization=row.avg_cpu or 0.0,
            avg_memory_utilization=row.avg_memory or 0.0,
            max_cpu_utilization=row.max_cpu or 0.0,
            max_memory_utilization=row.max_memory or 0.0,
            devices_sampled=row.devices_sampled or 0
        ))

    return results


@router.get("/report/packet-drops", response_model=List[schemas.PacketDropRecord])
async def get_report_packet_drops(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Get packet drop statistics by device for report date range.
    Returns devices with highest discard rates, including errors.
    """
    start_dt = datetime.datetime.fromisoformat(start_date)
    end_dt = datetime.datetime.fromisoformat(end_date)

    # Query to sum discards and errors per device over the period
    drop_stats = db.query(
        models.Device.hostname,
        models.Device.ip_address,
        func.sum(models.InterfaceMetric.discards_in).label('total_discards_in'),
        func.sum(models.InterfaceMetric.discards_out).label('total_discards_out'),
        func.sum(models.InterfaceMetric.errors_in).label('total_errors_in'),
        func.sum(models.InterfaceMetric.errors_out).label('total_errors_out'),
        func.sum(models.InterfaceMetric.octets_in + models.InterfaceMetric.octets_out).label('total_octets')
    ).join(
        models.Interface,
        models.Interface.device_id == models.Device.id
    ).join(
        models.InterfaceMetric,
        models.InterfaceMetric.interface_id == models.Interface.id
    ).filter(
        models.InterfaceMetric.timestamp >= start_dt,
        models.InterfaceMetric.timestamp <= end_dt
    ).group_by(
        models.Device.id,
        models.Device.hostname,
        models.Device.ip_address
    ).all()

    results = []
    for row in drop_stats:
        total_discards = (row.total_discards_in or 0) + (row.total_discards_out or 0)
        total_octets = row.total_octets or 1  # Avoid division by zero

        # Calculate discard rate as percentage
        discard_rate_pct = (total_discards / total_octets) * 100.0 if total_octets > 0 else 0.0

        # Only include devices with discards > 0
        if total_discards > 0:
            results.append(schemas.PacketDropRecord(
                device_hostname=row.hostname,
                device_ip=row.ip_address,
                discard_rate_pct=discard_rate_pct,
                total_discards_in=row.total_discards_in or 0.0,
                total_discards_out=row.total_discards_out or 0.0,
                total_errors_in=row.total_errors_in or 0.0,
                total_errors_out=row.total_errors_out or 0.0
            ))

    # Sort by discard rate descending, limit to top 10
    results.sort(key=lambda x: x.discard_rate_pct, reverse=True)
    return results[:10]


@router.get("/report/uptime-summary", response_model=schemas.UptimeSummaryResponse)
async def get_report_uptime_summary(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Get system uptime summary for report date range.
    Returns average uptime, longest uptime device, and recently rebooted device.
    """
    start_dt = datetime.datetime.fromisoformat(start_date)
    end_dt = datetime.datetime.fromisoformat(end_date)

    # Get average uptime per device in the period
    device_uptimes = db.query(
        models.Device.hostname,
        models.Device.ip_address,
        func.avg(models.DeviceMetric.uptime_seconds).label('avg_uptime_seconds')
    ).join(
        models.DeviceMetric,
        models.DeviceMetric.device_id == models.Device.id
    ).filter(
        models.DeviceMetric.timestamp >= start_dt,
        models.DeviceMetric.timestamp <= end_dt
    ).group_by(
        models.Device.id,
        models.Device.hostname,
        models.Device.ip_address
    ).all()

    if not device_uptimes:
        return schemas.UptimeSummaryResponse(
            avg_uptime_days=0.0,
            longest_uptime={"hostname": "N/A", "ip": "N/A", "uptime_days": 0.0},
            recently_rebooted={"hostname": "N/A", "ip": "N/A", "uptime_days": 0.0}
        )

    # Convert to days and calculate metrics
    uptime_data = []
    for row in device_uptimes:
        uptime_days = (row.avg_uptime_seconds or 0) / 86400.0  # seconds to days
        uptime_data.append({
            "hostname": row.hostname,
            "ip": row.ip_address,
            "uptime_days": uptime_days
        })

    # Calculate average across all devices
    avg_uptime_days = sum(d["uptime_days"] for d in uptime_data) / len(uptime_data)

    # Find longest and shortest uptime
    longest = max(uptime_data, key=lambda x: x["uptime_days"])
    recently_rebooted = min(uptime_data, key=lambda x: x["uptime_days"])

    return schemas.UptimeSummaryResponse(
        avg_uptime_days=avg_uptime_days,
        longest_uptime=longest,
        recently_rebooted=recently_rebooted
    )


@router.get("/report/availability", response_model=List[schemas.AvailabilityRecord])
async def get_report_availability(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    Get device availability metrics for report date range.
    Returns availability percentage based on reachability polls.
    """
    start_dt = datetime.datetime.fromisoformat(start_date)
    end_dt = datetime.datetime.fromisoformat(end_date)

    # Count reachability polls per device
    availability_stats = db.query(
        models.Device.hostname,
        models.Device.ip_address,
        func.count(models.DeviceMetric.id).label('total_polls'),
        func.sum(case((models.Device.is_reachable == True, 1), else_=0)).label('successful_polls'),
        func.avg(models.DeviceMetric.uptime_seconds).label('avg_uptime_seconds'),
        func.max(models.DeviceMetric.timestamp).label('last_seen')
    ).join(
        models.DeviceMetric,
        models.DeviceMetric.device_id == models.Device.id
    ).filter(
        models.DeviceMetric.timestamp >= start_dt,
        models.DeviceMetric.timestamp <= end_dt
    ).group_by(
        models.Device.id,
        models.Device.hostname,
        models.Device.ip_address
    ).all()

    results = []
    for row in availability_stats:
        total_polls = row.total_polls or 1  # Avoid division by zero
        successful_polls = row.successful_polls or 0

        # Calculate availability percentage
        availability_pct = (successful_polls / total_polls) * 100.0
        avg_uptime_days = (row.avg_uptime_seconds or 0) / 86400.0

        results.append(schemas.AvailabilityRecord(
            device_hostname=row.hostname,
            device_ip=row.ip_address,
            availability_pct=availability_pct,
            avg_uptime_days=avg_uptime_days,
            last_seen=to_utc_iso(row.last_seen) if row.last_seen else to_utc_iso(datetime.utcnow())
        ))

    # Sort by availability ascending (worst first)
    results.sort(key=lambda x: x.availability_pct)
    return results
