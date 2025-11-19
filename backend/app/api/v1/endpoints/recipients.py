from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core import database, models, schemas

router = APIRouter(prefix="/recipients", tags=["Recipients"])
get_db = database.get_db


@router.post("/", response_model=schemas.RecipientResponse, status_code=status.HTTP_201_CREATED)
def create_recipient(
    recipient: schemas.RecipientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new alert recipient
    """
    # Check if email already exists
    existing_recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.email == recipient.email
    ).first()

    if existing_recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recipient with email {recipient.email} already exists"
        )

    # Create new recipient
    db_recipient = models.AlertRecipient(email=recipient.email)
    db.add(db_recipient)
    db.commit()
    db.refresh(db_recipient)

    return db_recipient


@router.get("/", response_model=List[schemas.RecipientResponse])
def get_all_recipients(db: Session = Depends(get_db)):
    """
    Retrieve all alert recipients
    """
    recipients = db.query(models.AlertRecipient).all()
    return recipients


@router.get("/{recipient_id}", response_model=schemas.RecipientResponse)
def get_recipient(recipient_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific recipient by ID
    """
    recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.id == recipient_id
    ).first()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with id {recipient_id} not found"
        )

    return recipient


@router.put("/{recipient_id}", response_model=schemas.RecipientResponse)
def update_recipient(
    recipient_id: int,
    recipient: schemas.RecipientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing recipient's email
    """
    db_recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.id == recipient_id
    ).first()

    if not db_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with id {recipient_id} not found"
        )

    # Check if new email already exists (but not for the current recipient)
    existing_recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.email == recipient.email,
        models.AlertRecipient.id != recipient_id
    ).first()

    if existing_recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recipient with email {recipient.email} already exists"
        )

    # Update recipient
    db_recipient.email = recipient.email
    db.commit()
    db.refresh(db_recipient)

    return db_recipient


@router.delete("/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    """
    Delete a recipient by ID
    """
    db_recipient = db.query(models.AlertRecipient).filter(
        models.AlertRecipient.id == recipient_id
    ).first()

    if not db_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with id {recipient_id} not found"
        )

    db.delete(db_recipient)
    db.commit()

    return None
