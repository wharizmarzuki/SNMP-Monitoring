import asyncio
import ipaddress
from sqlalchemy.orm import Session
from app.core import database, models, schemas
from services.snmp_service import SNMPClient, device_discovery
from services.device_service import DeviceRepository, SQLAlchemyDeviceRepository
from app.config.settings import settings
from app.config.logging import logger

def get_repository(db: Session) -> DeviceRepository:
    """Creates a repository instance for the discovery to use."""
    return SQLAlchemyDeviceRepository(db)

async def perform_full_discovery(db: Session, client: SNMPClient, network: str, subnet: str):
    """
    Scans an entire network subnet and updates/adds devices to the database.

    Each concurrent discovery task gets its own database session to avoid
    SQLAlchemy session sharing issues and SQLite lock contention.
    """
    logger.info(f"Starting background discovery scan on {network}/{subnet}...")

    try:
        network_addr = ipaddress.IPv4Network(f"{network}/{subnet}", strict=False)
        host_addresses = [str(ip) for ip in network_addr.hosts()]
    except ValueError as e:
        logger.error(f"Invalid network/subnet provided for discovery: {e}")
        return {"total_scanned": 0, "devices_found": 0, "devices": []}  # Return an empty result

    semaphore = asyncio.Semaphore(settings.discovery_concurrency)

    async def limited_discovery(ip):
        """
        Each task gets its own database session to avoid race conditions.

        This follows SQLAlchemy best practices: one session per task.
        Each discovery operation independently commits its device update.
        """
        async with semaphore:
            # Create a NEW session for this discovery task
            task_db = database.SessionLocal()
            try:
                # Create repository with this task's dedicated session
                task_repo = get_repository(task_db)
                result = await device_discovery(ip, client, task_repo)
                return result
            except Exception as e:
                logger.error(f"Error during discovery of {ip}: {e}")
                task_db.rollback()
                return None
            finally:
                # Always close the session
                task_db.close()

    tasks = [limited_discovery(ip) for ip in host_addresses]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and None values
    reachable_devices = [device for device in results if device is not None and not isinstance(device, Exception)]

    logger.info(f"Discovery complete: Found {len(reachable_devices)} new/updated devices out of {len(host_addresses)} scanned.")
    return {
        "total_scanned": len(host_addresses),
        "devices_found": len(reachable_devices),
        "devices": reachable_devices
    }