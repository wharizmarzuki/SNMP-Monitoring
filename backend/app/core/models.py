from datetime import datetime
from typing import List 
from sqlalchemy import BigInteger, String, Integer, Float, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    ip_address: Mapped[str | None] = mapped_column(String, unique=True)
    hostname: Mapped[str | None] = mapped_column(String, unique=True)
    mac_address: Mapped[str | None] = mapped_column(String, index=True)
    vendor: Mapped[str | None] = mapped_column(String)
    priority: Mapped[int | None] = mapped_column(Integer)

    # Thresholds
    cpu_threshold: Mapped[float] = mapped_column(Float, default=80.0)
    memory_threshold: Mapped[float] = mapped_column(Float, default=80.0)
    failure_threshold: Mapped[int] = mapped_column(Integer, default=3)

    # Alert state management (Phase 2)
    cpu_alert_state: Mapped[str] = mapped_column(String, default="clear")  # clear/triggered/acknowledged
    cpu_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memory_alert_state: Mapped[str] = mapped_column(String, default="clear")
    memory_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reachability_alert_state: Mapped[str] = mapped_column(String, default="clear")
    reachability_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Legacy boolean flags (deprecated, kept for backward compatibility)
    cpu_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reachability_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Maintenance mode (device-level only)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    maintenance_reason: Mapped[str | None] = mapped_column(String)

    # Poll tracking
    last_poll_attempt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_poll_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    is_reachable: Mapped[bool] = mapped_column(Boolean, default=True)

    metrics: Mapped[list["DeviceMetric"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    interfaces: Mapped[list["Interface"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class DeviceMetric(Base):
    __tablename__ = "device_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    cpu_utilization: Mapped[float | None] = mapped_column(Float)
    memory_utilization: Mapped[float | None] = mapped_column(Float)
    uptime_seconds: Mapped[int | None] = mapped_column(BigInteger) 
    
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    
    device: Mapped["Device"] = relationship(back_populates="metrics")


class Interface(Base):
    __tablename__ = "interfaces"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    
    if_index: Mapped[int | None] = mapped_column(Integer, index=True)
    if_name: Mapped[str | None] = mapped_column(String, index=True)

    packet_drop_threshold: Mapped[float] = mapped_column(Float, default=0.1)  # Percentage: 0.1% default

    # Alert state management (Phase 2)
    oper_status_alert_state: Mapped[str] = mapped_column(String, default="clear")
    oper_status_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    packet_drop_alert_state: Mapped[str] = mapped_column(String, default="clear")
    packet_drop_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Legacy boolean flags (deprecated, kept for backward compatibility)
    packet_drop_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    oper_status_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    device: Mapped["Device"] = relationship(back_populates="interfaces")
    
    metrics: Mapped[list["InterfaceMetric"]] = relationship(
        back_populates="interface", cascade="all, delete-orphan"
    )


class InterfaceMetric(Base):
    __tablename__ = "interface_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interface_id: Mapped[int] = mapped_column(ForeignKey("interfaces.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Status codes are integers
    admin_status: Mapped[int | None] = mapped_column(Integer)
    oper_status: Mapped[int | None] = mapped_column(Integer)
    
    # Counters
    octets_in: Mapped[float | None] = mapped_column(Float)
    octets_out: Mapped[float | None] = mapped_column(Float)
    errors_in: Mapped[float | None] = mapped_column(Float)
    errors_out: Mapped[float | None] = mapped_column(Float)
    discards_in: Mapped[float | None] = mapped_column(Float)
    discards_out: Mapped[float | None] = mapped_column(Float)
    
    interface: Mapped["Interface"] = relationship(back_populates="metrics")


class AlertRecipient(Base):
    __tablename__ = "alert_recipients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)