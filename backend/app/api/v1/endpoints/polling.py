import asyncio
import typing
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import database, models
from app.core.security import get_current_user
from services.snmp_service import SNMPClient, get_snmp_client
from app.config.logging import logger

from services.polling_service import perform_full_poll
from services.polling_state import get_polling_state

router = APIRouter(
    prefix="/polling",
    tags=["Polling"],
    dependencies=[Depends(get_current_user)]  # Require authentication for all polling endpoints
)
get_db = database.get_db


@router.get("/status")
async def get_polling_status():
    """
    Get the current polling status.
    Returns whether polling is currently active and the type of polling.
    """
    polling_state = get_polling_state()
    return await polling_state.get_status()


@router.get("/")
async def poll_all_device_api(db: Session = Depends(get_db)):
    """
    API Endpoint to manually trigger a full device poll.
    This is now a "dumb" wrapper that calls the polling service.
    """
    polling_state = get_polling_state()

    # Check if polling is already running
    if await polling_state.is_polling():
        raise HTTPException(status_code=409, detail="Polling already in progress")

    try:
        # Mark polling as active
        await polling_state.start_polling(polling_type="manual")

        # Get SNMP client with runtime settings from database
        client = get_snmp_client(db)

        # This endpoint is now just a simple wrapper
        await perform_full_poll(db, client)
        return {"message": "Full device poll triggered successfully."}
    except Exception as e:
        logger.error(f"Error during manual poll: {e}")
        raise HTTPException(status_code=500, detail="Polling failed")
    finally:
        # Always mark polling as complete
        await polling_state.end_polling()
