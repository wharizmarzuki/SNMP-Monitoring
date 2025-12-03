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
    dependencies=[Depends(get_current_user)]
)
get_db = database.get_db


@router.get("/status")
async def get_polling_status():
    """Get current polling status and type."""
    polling_state = get_polling_state()
    return await polling_state.get_status()


@router.get("/")
async def poll_all_device_api(db: Session = Depends(get_db)):
    """Manually trigger full device poll."""
    polling_state = get_polling_state()

    if await polling_state.is_polling():
        raise HTTPException(status_code=409, detail="Polling already in progress")

    try:
        await polling_state.start_polling(polling_type="manual")
        client = get_snmp_client(db)
        await perform_full_poll(db, client)
        return {"message": "Full device poll triggered successfully."}
    except Exception as e:
        logger.error(f"Error during manual poll: {e}")
        raise HTTPException(status_code=500, detail="Polling failed")
    finally:
        await polling_state.end_polling()
