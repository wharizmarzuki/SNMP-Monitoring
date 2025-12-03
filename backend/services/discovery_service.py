"""
Network discovery service - SNMP-based device scanning.
Handles concurrent network scanning and device registration.
"""
import asyncio
import ipaddress
from sqlalchemy.orm import Session
from app.core import database, models, schemas
from services.snmp_service import SNMPClient, device_discovery
from services.device_service import DeviceRepository, SQLAlchemyDeviceRepository
from app.config.settings import settings, get_runtime_settings
from app.config.logging import logger


def get_repository(db: Session) -> DeviceRepository:
    """Create repository instance for discovery operations."""
    return SQLAlchemyDeviceRepository(db)


async def perform_full_discovery(db: Session, client: SNMPClient, network: str, subnet: str):
    """
    Scan network subnet and register discovered devices.
    Each discovery task uses dedicated database session.
    """
    logger.info(f"Starting background discovery scan on {network}/{subnet}...")

    runtime_config = get_runtime_settings(db)
    discovery_concurrency = runtime_config["discovery_concurrency"]

    try:
        network_addr = ipaddress.IPv4Network(f"{network}/{subnet}", strict=False)
        host_addresses = [str(ip) for ip in network_addr.hosts()]
    except ValueError as e:
        logger.error(f"Invalid network/subnet provided for discovery: {e}")
        return {"total_scanned": 0, "devices_found": 0, "devices": []}

    semaphore = asyncio.Semaphore(discovery_concurrency)

    async def limited_discovery(ip):
        """Discover single device with dedicated database session."""
        async with semaphore:
            task_db = database.SessionLocal()
            try:
                task_repo = get_repository(task_db)
                result = await device_discovery(ip, client, task_repo)
                return result
            except Exception as e:
                logger.error(f"Error during discovery of {ip}: {e}")
                task_db.rollback()
                return None
            finally:
                task_db.close()

    tasks = [limited_discovery(ip) for ip in host_addresses]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    reachable_devices = [device for device in results if device is not None and not isinstance(device, Exception)]

    logger.info(f"Discovery complete: Found {len(reachable_devices)} new/updated devices out of {len(host_addresses)} scanned.")
    return {
        "total_scanned": len(host_addresses),
        "devices_found": len(reachable_devices),
        "devices": reachable_devices
    }