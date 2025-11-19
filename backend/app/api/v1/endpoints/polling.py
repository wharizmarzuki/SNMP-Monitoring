import asyncio
import typing
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import database, models
from services.snmp_service import SNMPClient, get_snmp_client
from app.config.logging import logger

from services.polling_service import perform_full_poll 

router = APIRouter(prefix="/polling", tags=["Polling"])
get_db = database.get_db


@router.get("/")
async def poll_all_device_api(db: Session = Depends(get_db), client: SNMPClient = Depends(get_snmp_client)):
    """
    API Endpoint to manually trigger a full device poll.
    This is now a "dumb" wrapper that calls the polling service.
    """
    try:
        # This endpoint is now just a simple wrapper
        await perform_full_poll(db, client)
        return {"message": "Full device poll triggered successfully."}
    except Exception as e:
        logger.error(f"Error during manual poll: {e}")
        raise HTTPException(status_code=500, detail="Polling failed")
