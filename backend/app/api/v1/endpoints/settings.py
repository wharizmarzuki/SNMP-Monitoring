from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core import database, models, schemas
from app.core.security import get_current_user
from app.config.settings import get_settings

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(get_current_user)]  # Require authentication for all settings endpoints
)
get_db = database.get_db


@router.get("/", response_model=schemas.ApplicationSettingsResponse)
def get_application_settings(db: Session = Depends(get_db)):
    """
    Get current application settings from database.
    If no settings exist in DB, create default settings from .env.
    """
    settings = db.query(models.ApplicationSettings).first()

    if not settings:
        # Initialize settings from .env defaults
        env_settings = get_settings()
        settings = models.ApplicationSettings(
            snmp_community=env_settings.SNMP_COMMUNITY,
            snmp_timeout=env_settings.SNMP_TIMEOUT,
            snmp_retries=env_settings.SNMP_RETRIES,
            polling_interval=env_settings.POLLING_INTERVAL,
            discovery_concurrency=env_settings.DISCOVERY_CONCURRENCY,
            polling_concurrency=env_settings.POLLING_CONCURRENCY,
            smtp_server=env_settings.SMTP_SERVER,
            smtp_port=env_settings.SMTP_PORT,
            sender_email=env_settings.SENDER_EMAIL,
            sender_password=env_settings.SENDER_PASSWORD,
            discovery_network=env_settings.DISCOVERY_NETWORK
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Mask the password in response
    response = schemas.ApplicationSettingsResponse.model_validate(settings)
    if response.sender_password:
        response.sender_password = "********"

    return response


@router.patch("/", response_model=schemas.ApplicationSettingsResponse)
def update_application_settings(
    updates: schemas.ApplicationSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application settings. Only provided fields will be updated.
    """
    settings = db.query(models.ApplicationSettings).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not initialized. Please call GET /settings first."
        )

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    # Mask the password in response
    response = schemas.ApplicationSettingsResponse.model_validate(settings)
    if response.sender_password:
        response.sender_password = "********"

    return response
