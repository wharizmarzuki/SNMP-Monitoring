from fastapi import HTTPException
from typing import Dict, Any, Optional


class APIError(HTTPException):
    """Base API error with consistent format"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": self.details
            }
        )


class DeviceNotFoundError(APIError):
    """Raised when a device is not found"""
    def __init__(self, ip: str):
        super().__init__(
            status_code=404,
            error_code="DEVICE_NOT_FOUND",
            message=f"Device with IP {ip} not found"
        )


class InterfaceNotFoundError(APIError):
    """Raised when an interface is not found"""
    def __init__(self, ip: str, if_index: int):
        super().__init__(
            status_code=404,
            error_code="INTERFACE_NOT_FOUND",
            message=f"Interface {if_index} not found on device {ip}"
        )


class ValidationError(APIError):
    """Raised when input validation fails"""
    def __init__(self, field: str, error: str):
        super().__init__(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="Invalid input data",
            details={"field": field, "error": error}
        )


class SNMPConnectionError(APIError):
    """Raised when SNMP connection fails"""
    def __init__(self, ip: str, reason: str):
        super().__init__(
            status_code=503,
            error_code="SNMP_CONNECTION_FAILED",
            message=f"Failed to connect to device {ip}",
            details={"reason": reason}
        )


class DatabaseError(APIError):
    """Raised when database operations fail"""
    def __init__(self, operation: str):
        super().__init__(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=f"Database operation failed: {operation}"
        )


class AlertNotFoundError(APIError):
    """Raised when trying to acknowledge/resolve a non-existent alert"""
    def __init__(self, alert_type: str):
        super().__init__(
            status_code=400,
            error_code="ALERT_NOT_FOUND",
            message=f"No active {alert_type} alert to acknowledge or resolve"
        )


class DiscoveryError(APIError):
    """Raised when network discovery fails"""
    def __init__(self, reason: str):
        super().__init__(
            status_code=500,
            error_code="DISCOVERY_FAILED",
            message="Network discovery failed",
            details={"reason": reason}
        )
