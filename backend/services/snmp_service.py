import asyncio
from typing import Optional
from venv import logger
from fastapi import Depends
from sqlalchemy.orm import Session
from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd,
    bulk_cmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
)
from app.core import database
from app.config.settings import settings, get_runtime_settings
from app.core import schemas
from abc import ABC, abstractmethod
from services.device_service import DeviceRepository, SQLAlchemyDeviceRepository, update_device

COMMUNITY = settings.snmp_community

def get_repository(db: Session = Depends(database.get_db)) -> DeviceRepository:
    return SQLAlchemyDeviceRepository(db)


class SNMPClient(ABC):
    @abstractmethod
    async def get(self, host: str, oids: list[str]) -> Optional[dict]:
        pass

    @abstractmethod
    async def bulk_walk(self, host: str, oids: list[str]) -> dict:
        pass


def get_snmp_client(db_session: Optional[Session] = None) -> SNMPClient:
    """
    Get SNMP client with runtime settings.
    If db_session is provided, uses database settings; otherwise uses .env defaults.
    """
    runtime_config = get_runtime_settings(db_session)
    return PySNMPClient(
        community=runtime_config["snmp_community"],
        timeout=runtime_config["snmp_timeout"],
        retries=runtime_config["snmp_retries"]
    )


class PySNMPClient(SNMPClient):
    def __init__(self, community: str = COMMUNITY, timeout: int = 10, retries: int = 3):
        self.community = community
        self.timeout = timeout
        self.retries = retries
    
    async def get(self, host: str, oids: list[str]) -> Optional[dict]:
        port = 161
        transport_address = (host, port)
        try:
            snmpEngine = SnmpEngine()
            oid_objects = [ObjectType(ObjectIdentity(oid)) for oid in oids]
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                snmpEngine,
                CommunityData(self.community, mpModel=1),
                await UdpTransportTarget.create(transport_address),
                ContextData(),
                *oid_objects,
            )

            if errorIndication or errorStatus or not varBinds:
                return None

            processed_data = []
            for varBind in varBinds:
                try:
                    oid_name = (
                        str(varBind[0]).split("::", 1)[1]
                        if "::" in str(varBind[0])
                        else str(varBind[0])
                    )
                    value = varBind[1].prettyPrint()
                    processed_data.append(
                        {"oid": oid_name, "value": value, "raw": f"{oid_name} = {value}"}
                    )
                except Exception:
                    continue

            return {
                "success": True,
                "host": transport_address[0],
                "data": processed_data,
                "raw_data": [item["raw"] for item in processed_data],
            }
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None
    
    async def bulk_walk(self, host: str, oids: list[str]) -> dict:
        port = 161
        transport_address = (host, port)
        snmp_engine = SnmpEngine()

        # Store the base OIDs we're walking to detect when we've exited the table
        base_oids = set(oids)

        results = []
        oid_objects = [ObjectType(ObjectIdentity(oid)) for oid in oids]

        try:
            while True:
                errorIndication, errorStatus, errorIndex, varBindTable = await bulk_cmd(
                    snmp_engine,
                    CommunityData(self.community, mpModel=1),
                    await UdpTransportTarget.create(transport_address),
                    ContextData(),
                    0, 50,  # Increased max-repetitions for better performance
                    *oid_objects
                )

                if errorIndication:
                    return {"success": False, "error": str(errorIndication)}

                if errorStatus:
                    return {"success": False, "error": f"{errorStatus.prettyPrint()} at {errorIndex and varBindTable[int(errorIndex) - 1][0] or '?'}"} # type: ignore

                # No more data
                if not varBindTable:
                    break

                # Track if we're still within our target OID tree
                still_in_table = False
                last_oids = {}

                for var_bind in varBindTable:
                    full_oid = '.'.join(str(x) for x in var_bind[0].asTuple())

                    # Check if this OID is still under one of our base OIDs
                    is_child = False
                    for base_oid in base_oids:
                        if full_oid.startswith(base_oid + '.'):
                            is_child = True
                            still_in_table = True
                            # Track the last OID for each base to continue from
                            last_oids[base_oid] = var_bind[0]
                            break

                    # Only process if it's a child of our base OIDs
                    if is_child:
                        oid_parts = full_oid.split('.')
                        base_oid = '.'.join(oid_parts[:-1])
                        index = oid_parts[-1]
                        value = var_bind[1].prettyPrint()

                        results.append({
                            "base_oid": base_oid,
                            "index": index,
                            "value": value
                        })

                # If we've exited all our OID trees, we're done
                if not still_in_table:
                    break

                # Continue from the last OIDs received
                oid_objects = [ObjectType(last_oids[base_oid]) for base_oid in base_oids if base_oid in last_oids]

                # Safety check: if no valid OIDs to continue, break
                if not oid_objects:
                    break

            return {"success": True, "data": results}

        except Exception as e:
            return {"success": False, "error": str(e)}


async def get_snmp_data(
    host: str,
    oids: list[str],
    snmp_client: SNMPClient
) -> Optional[dict]:
    """Service function for SNMP GET operations"""
    return await snmp_client.get(host, oids)


async def bulk_snmp_walk(
    host: str,
    oids: list[str],
    snmp_client: SNMPClient
) -> dict:
    """Service function for SNMP BULK WALK operations"""
    return await snmp_client.bulk_walk(host, oids)


async def device_discovery(
    host: str,
    snmp_client: SNMPClient = Depends(get_snmp_client),  # Add Depends
    repo: DeviceRepository = Depends(get_repository) 
) -> Optional[schemas.DeviceInfo]:
    oids = list(schemas.DISCOVERY_OIDS.values())
    result = await snmp_client.get(host, oids) 

    if result and result.get("success"):
        data = result["data"]
        oid_values = {}

        for i, (key, oid) in enumerate(schemas.DISCOVERY_OIDS.items()):
            oid_values[key] = data[i]["value"] if i < len(data) else None

        device_info = schemas.DeviceInfo(
            ip_address=host,
            **oid_values,
        )
        
        try:
            await update_device(device_info, repo) 
            return device_info
        except Exception as e:
            logger.error(f"Error saving device {host}: {e}")
            return device_info

    return None