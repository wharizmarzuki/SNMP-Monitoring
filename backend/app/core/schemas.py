from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List


class DeviceInfo(BaseModel):
    ip_address: str = Field(..., description="Device IP address")
    hostname: str = Field(default="Unknown", description="Device system name")
    mac_address:str = Field(..., description="Device MAC address")
    vendor:str = Field(default="N/A", description="Vendor")
    priority:int = Field(default=1, description="Priority")

    # Poll tracking fields
    last_poll_attempt: datetime | None = None
    last_poll_success: datetime | None = None
    consecutive_failures: int = 0
    is_reachable: bool = True

    # Thresholds
    cpu_threshold: float = Field(default=80.0)
    memory_threshold: float = Field(default=80.0)
    failure_threshold: int = Field(default=3)

    # Alert state (Phase 2)
    cpu_alert_state: str = "clear"
    memory_alert_state: str = "clear"
    reachability_alert_state: str = "clear"
    cpu_acknowledged_at: datetime | None = None
    memory_acknowledged_at: datetime | None = None
    reachability_acknowledged_at: datetime | None = None

    # Legacy alert flags (deprecated)
    reachability_alert_sent: bool = False

    # Maintenance mode (Phase 2)
    maintenance_mode: bool = False
    maintenance_until: datetime | None = None
    maintenance_reason: str | None = None

    status: str = Field(default="up")

    model_config = ConfigDict(from_attributes=True)


class DeviceResponse(BaseModel):
    """DTO for device responses - stable API contract"""
    id: int
    ip_address: str
    hostname: str
    vendor: str | None
    is_reachable: bool
    cpu_threshold: float
    memory_threshold: float
    failure_threshold: int
    cpu_alert_state: str
    memory_alert_state: str
    reachability_alert_state: str
    maintenance_mode: bool
    last_poll_success: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DeviceMetrics(BaseModel):
    # This schema now matches the 'oid_values' dict in polling_service.py
    device_id: int
    uptime: str | float | int 
    device_name: str | None = Field(default="Unknown")
    model_name: str | None = Field(default="N/A")
    cpu_utilization: float = Field(default=0)
    memory_utilization: float = Field(default=0)


class DiscoveryResponse(BaseModel):
    total_scanned: int = Field(..., description="Total IPs scanned")
    devices_found: int = Field(..., description="Number of responsive devices")
    devices: List[DeviceInfo] = Field(..., description="List of discovered devices")

class InterfaceMetric(BaseModel):
    index: int
    name: str
    admin_status: int
    oper_status: int
    octets_in: float
    octets_out: float
    errors_in: float
    errors_out: float
    discards_in: float
    discards_out: float

class PaginatedInterfaces(BaseModel):
    host: str
    interfaces: List[InterfaceMetric]
    page: int
    per_page: int
    total: int


DISCOVERY_OIDS = {
    "hostname": "1.3.6.1.2.1.1.5.0",
    "mac_address": "1.3.6.1.2.1.2.2.1.6.1",
    "vendor": "1.3.6.1.2.1.1.2.0",
}

VENDOR_MAPPING = {
    9: "Cisco",
    11: "HP", 
    43: "3Com",
    2636: "Juniper",
    8072: "Net-SNMP",
    311: "Microsoft",
    2021: "UCD-SNMP",
    674: "Dell",
}

DEVICE_OIDS = {
    "uptime": "1.3.6.1.2.1.1.3.0",
    "device_name": "1.3.6.1.2.1.1.5.0",
    "model_name": "1.3.6.1.2.1.47.1.1.1.1.13.1",
}

INTERFACE_OIDS = {
    "interface_index": "1.3.6.1.2.1.2.2.1.1",
    "interface_description": "1.3.6.1.2.1.2.2.1.2",
    "interface_admin_status": "1.3.6.1.2.1.2.2.1.7",
    "interface_operational_status": "1.3.6.1.2.1.2.2.1.8",
    "inbound_octets": "1.3.6.1.2.1.2.2.1.10",
    "outbound_octets": "1.3.6.1.2.1.2.2.1.16",
    "inbound_errors": "1.3.6.1.2.1.2.2.1.14",
    "outbound_errors": "1.3.6.1.2.1.2.2.1.20",
    "inbound_discards": "1.3.6.1.2.1.2.2.1.13",
    "outbound_discards": "1.3.6.1.2.1.2.2.1.19",
}

VENDOR_OIDS = {
    "Cisco": {
        "cpu_utilization": "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1",
        "memory_pool_1": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
        "memory_pool_2": "1.3.6.1.4.1.9.9.48.1.1.1.5.2",
        "memory_pool_13": "1.3.6.1.4.1.9.9.48.1.1.1.5.13",
    },
}


class RecipientCreate(BaseModel):
    email: str = Field(..., description="Recipient email address")


class RecipientUpdate(BaseModel):
    email: str = Field(..., description="Updated recipient email address")


class RecipientResponse(BaseModel):
    id: int = Field(..., description="Recipient ID")
    email: str = Field(..., description="Recipient email address")
    model_config = ConfigDict(from_attributes=True)


class ThresholdUpdate(BaseModel):
    threshold_value: float = Field(..., description="Threshold value (percentage)", ge=0, le=100)


class FailureThresholdUpdate(BaseModel):
    threshold_value: int = Field(..., description="Number of consecutive failures before marking device unreachable", ge=1, le=10)


class InterfaceThresholdUpdate(BaseModel):
    """Schema for updating interface packet drop thresholds (not limited to 100)"""
    threshold_value: float = Field(..., description="Packet drop threshold (number of drops)", ge=0)


class ThresholdBatchUpdate(BaseModel):
    """Batch threshold update matching frontend payload"""
    cpu_threshold: float | None = Field(None, ge=0, le=100)
    memory_threshold: float | None = Field(None, ge=0, le=100)
    failure_threshold: int | None = Field(None, ge=1, le=10)


class ThresholdResponse(BaseModel):
    ip_address: str = Field(..., description="Device IP address")
    cpu_threshold: float = Field(..., description="CPU threshold value")
    memory_threshold: float = Field(..., description="Memory threshold value")
    failure_threshold: int = Field(..., description="Failure threshold value")
    model_config = ConfigDict(from_attributes=True)


class AlertSentUpdate(BaseModel):
    alert_sent: bool = Field(..., description="Alert sent status (true/false)")


class AlertSentResponse(BaseModel):
    ip_address: str = Field(..., description="Device IP address")
    cpu_alert_sent: bool = Field(..., description="CPU alert sent status")
    memory_alert_sent: bool = Field(..., description="Memory alert sent status")
    model_config = ConfigDict(from_attributes=True)


# Phase 2: Alert state management schemas
class AlertAcknowledge(BaseModel):
    notes: str | None = Field(default=None, description="Optional notes about acknowledgment")


class AlertResolve(BaseModel):
    reason: str | None = Field(default=None, description="Reason for resolving alert")


class MaintenanceModeUpdate(BaseModel):
    enabled: bool = Field(..., description="Enable/disable maintenance mode")
    duration_minutes: int = Field(default=60, ge=1, le=1440, description="Maintenance window duration (1-1440 minutes)")
    reason: str | None = Field(default=None, description="Reason for maintenance")


class AlertStateResponse(BaseModel):
    message: str = Field(..., description="Response message")
    state: str = Field(..., description="Current alert state (clear/triggered/acknowledged)")
    acknowledged_at: datetime | None = Field(default=None, description="When alert was acknowledged")


class NetworkSummaryResponse(BaseModel):
    """
    For the main dashboard's KPI cards.
    """
    total_devices: int
    devices_in_alert: int
    devices_up: int

class DeviceMetricResponse(BaseModel):
    """
    For returning historical metric data for charts.
    """
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    uptime_seconds: int

    model_config = ConfigDict(from_attributes=True)

class InterfaceMetricResponse(BaseModel):
    """
    For returning the latest status of an interface.
    """
    id: int
    timestamp: datetime
    admin_status: int
    oper_status: int
    octets_in: float
    octets_out: float
    errors_in: float
    errors_out: float
    discards_in: float
    discards_out: float

    # Joined from the parent Interface model
    if_name: str | None = None
    if_index: int | None = None
    packet_drop_threshold: float | None = None

    model_config = ConfigDict(from_attributes=True)


class InterfaceSummaryResponse(BaseModel):
    """Lightweight interface data (only fields used by frontend)"""
    if_index: int
    if_name: str
    if_descr: str | None
    oper_status: int
    admin_status: int
    octets_in: int | None
    octets_out: int | None
    discards_in: int | None
    discards_out: int | None
    errors_in: int | None
    errors_out: int | None

    model_config = ConfigDict(from_attributes=True)

class ActiveAlertResponse(BaseModel):
    hostname: str
    ip_address: str
    metric: str
    current_value: str
    threshold: str
    state: str = "triggered"  # Phase 2: clear/triggered/acknowledged
    acknowledged_at: datetime | None = None  # Phase 2: When acknowledged
    if_index: int | None = None  # For interface alerts only

class TopDeviceResponse(BaseModel):
    """
    For the dashboard bar charts.
    """
    hostname: str
    ip_address: str
    value: float

class HistoryQuery(BaseModel):
    ip_address: str
    start_time: datetime
    end_time: datetime

class ThroughputDatapoint(BaseModel):
    timestamp: datetime
    inbound_bps: float
    outbound_bps: float

class InterfaceThresholdResponse(BaseModel):
    id: int
    device_id: int
    if_index: int
    if_name: str | None
    packet_drop_threshold: float
    model_config = ConfigDict(from_attributes=True)