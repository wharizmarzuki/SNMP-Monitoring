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
    "interface_speed": "1.3.6.1.2.1.2.2.1.5",  # ifSpeed (bps, max ~4 Gbps)
    "interface_high_speed": "1.3.6.1.2.1.31.1.1.1.15",  # ifHighSpeed (Mbps, for Gigabit+)
    "interface_admin_status": "1.3.6.1.2.1.2.2.1.7",
    "interface_operational_status": "1.3.6.1.2.1.2.2.1.8",
    # High-Capacity (64-bit) octet counters - prevents wrap on Gigabit+ interfaces
    "inbound_octets": "1.3.6.1.2.1.31.1.1.1.6",   # ifHCInOctets (64-bit)
    "outbound_octets": "1.3.6.1.2.1.31.1.1.1.10",  # ifHCOutOctets (64-bit)
    "inbound_errors": "1.3.6.1.2.1.2.2.1.14",
    "outbound_errors": "1.3.6.1.2.1.2.2.1.20",
    "inbound_discards": "1.3.6.1.2.1.2.2.1.13",
    "outbound_discards": "1.3.6.1.2.1.2.2.1.19",
    # Packet counters - High-capacity (64-bit) unicast packet counters for discard rate calculation
    "inbound_packets": "1.3.6.1.2.1.31.1.1.1.7",   # ifHCInUcastPkts (unicast packets received)
    "outbound_packets": "1.3.6.1.2.1.31.1.1.1.11",  # ifHCOutUcastPkts (unicast packets transmitted)
}

VENDOR_OIDS = {
    "Cisco": {
        # CPU - Use cpmCPUTotal5minRev (non-deprecated, full 0-100% range)
        "cpu_utilization": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1",

        # Memory - Use Pool 1 (Processor Memory) for universal compatibility
        # Pool 1 exists on all Cisco routers and switches
        "memory_pool_used": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",  # ciscoMemoryPoolUsed.1
        "memory_pool_free": "1.3.6.1.4.1.9.9.48.1.1.1.6.1",  # ciscoMemoryPoolFree.1
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
    """Schema for updating interface discard rate thresholds (percentage-based)"""
    threshold_value: float = Field(..., description="Discard rate threshold (percentage: 0-100)", ge=0, le=100)


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


class AlertAction(BaseModel):
    """Schema for consolidated alert management endpoint"""
    action: str = Field(..., description="Action to perform: 'acknowledge' or 'resolve'")
    notes: str | None = Field(default=None, description="Optional notes about the action")
    reason: str | None = Field(default=None, description="Reason for resolving (only for resolve action)")


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
    devices_down: int

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
    packet_drop_threshold: float
    discard_rate_pct: float | None = None  # Calculated discard rate percentage (delta-based)

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
    severity: str = "Warning"  # Severity level: Warning, High, Critical

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

class DeviceUtilizationDatapoint(BaseModel):
    """Per-device throughput and utilization metrics."""
    device_id: int
    hostname: str | None
    ip_address: str | None
    timestamp: datetime

    # Raw throughput
    inbound_bps: float
    outbound_bps: float

    # Utilization metrics
    total_capacity_bps: int | None  # Sum of all interface speeds
    utilization_in_pct: float | None
    utilization_out_pct: float | None
    max_utilization_pct: float | None  # Max of in/out

class InterfaceThresholdResponse(BaseModel):
    id: int
    device_id: int
    if_index: int
    if_name: str | None
    packet_drop_threshold: float
    model_config = ConfigDict(from_attributes=True)


class ApplicationSettingsResponse(BaseModel):
    """Response schema for application settings"""
    id: int
    # SNMP Settings
    snmp_community: str
    snmp_timeout: int
    snmp_retries: int
    # Polling Settings
    polling_interval: int
    discovery_concurrency: int
    polling_concurrency: int
    # Email/SMTP Settings
    smtp_server: str
    smtp_port: int
    sender_email: str | None
    sender_password: str | None  # Will be masked in response
    # Network Discovery
    discovery_network: str | None
    # Timestamps
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationSettingsUpdate(BaseModel):
    """Update schema for application settings - all fields optional"""
    # SNMP Settings
    snmp_community: str | None = None
    snmp_timeout: int | None = Field(None, ge=1, le=60)
    snmp_retries: int | None = Field(None, ge=0, le=10)
    # Polling Settings
    polling_interval: int | None = Field(None, ge=10, le=3600)
    discovery_concurrency: int | None = Field(None, ge=1, le=100)
    polling_concurrency: int | None = Field(None, ge=1, le=100)
    # Email/SMTP Settings
    smtp_server: str | None = None
    smtp_port: int | None = Field(None, ge=1, le=65535)
    sender_email: str | None = None
    sender_password: str | None = None
    # Network Discovery
    discovery_network: str | None = None


# -------------------------------
# Report Schemas
# -------------------------------

class NetworkThroughputDatapoint(BaseModel):
    """Network-wide throughput data point for reports"""
    timestamp: datetime
    total_inbound_bps: float
    total_outbound_bps: float


class ReportDeviceUtilizationDatapoint(BaseModel):
    """Network-wide CPU/Memory utilization for reports"""
    timestamp: datetime
    avg_cpu_utilization: float
    avg_memory_utilization: float
    max_cpu_utilization: float
    max_memory_utilization: float
    devices_sampled: int


class PacketDropRecord(BaseModel):
    """Packet drop statistics by device for reports"""
    device_hostname: str
    device_ip: str
    discard_rate_pct: float
    total_discards_in: float
    total_discards_out: float
    total_errors_in: float
    total_errors_out: float


class UptimeSummaryResponse(BaseModel):
    """System uptime summary for reports"""
    avg_uptime_days: float
    longest_uptime: dict  # {hostname: str, ip: str, uptime_days: float}
    recently_rebooted: dict  # {hostname: str, ip: str, uptime_days: float}


class AvailabilityRecord(BaseModel):
    """Device availability metrics for reports"""
    device_hostname: str
    device_ip: str
    availability_pct: float
    avg_uptime_days: float
    last_seen: datetime