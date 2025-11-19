import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.endpoints import devices, polling, query, recipients
from app.core import models
from app.core.database import engine, SessionLocal
from app.core.exceptions import APIError
from services.snmp_service import get_snmp_client
from app.config.settings import settings
from app.config.logging import logger

from services.polling_service import perform_full_poll
from services.discovery_service import perform_full_discovery

models.Base.metadata.create_all(engine)


async def run_discovery_on_startup():
    """Run a single discovery scan on startup."""
    logger.info("Scheduling one-time discovery scan on startup...")
    await asyncio.sleep(5) 
    
    db: Session = SessionLocal()
    client = get_snmp_client()
    try:
        await perform_full_discovery(
            db, client, 
            network="192.168.254.1", 
            subnet="27"
        )
    except Exception as e:
        logger.error(f"Error during startup discovery: {e}")
        db.rollback()
    finally:
        db.close()
    logger.info("Startup discovery task finished.")


async def run_polling():
    """Run device polling every N seconds"""
    while True:
        logger.info(f"Background poller sleeping for {settings.polling_interval} seconds...")
        await asyncio.sleep(settings.polling_interval)
        
        logger.info("Background poller starting run...")
        db: Session = SessionLocal()
        client = get_snmp_client() 
        
        try:
            await perform_full_poll(db, client)
        except Exception as e:
            logger.error(f"Unhandled error in polling loop: {e}")
            db.rollback()
        finally:
            db.close()
            

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    
    asyncio.create_task(run_discovery_on_startup())
    
    logger.info("Starting background polling task...")
    polling_task = asyncio.create_task(run_polling())
    
    yield
    
    logger.info("Application shutting down...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        logger.info("Background polling task cancelled successfully.")

app = FastAPI(
    title="SNMP Device Monitor",
    description="SNMP device discovery and monitoring API",
    lifespan=lifespan
)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle all APIError exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)}
        }
    )


from app.api.middleware import add_middleware_to_app
add_middleware_to_app(app)

app.include_router(devices.router)
app.include_router(polling.router)
app.include_router(query.router)
app.include_router(recipients.router)