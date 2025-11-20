"""
Authentication and user management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.core.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password
)
from app.core.models import User

router = APIRouter()


# Pydantic schemas
class LoginRequest(BaseModel):
    """Login request body"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response"""
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info):
        if 'current_password' in info.data and v == info.data['current_password']:
            raise ValueError('New password must be different from current password')
        return v


class ChangeEmailRequest(BaseModel):
    """Change email request"""
    new_email: EmailStr
    password: str = Field(..., min_length=6, description="Current password for verification")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token

    - **username**: User's username
    - **password**: User's password

    Returns JWT access token valid for 24 hours
    """
    user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "admin": user.is_admin}
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header
    """
    return UserResponse.model_validate(current_user)


# User management endpoints
@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password

    - **current_password**: Current password for verification
    - **new_password**: New password (must be different from current)

    Requires valid JWT token in Authorization header
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return MessageResponse(message="Password changed successfully")


@router.put("/me/email", response_model=MessageResponse)
async def change_email(
    email_data: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's email address

    - **new_email**: New email address
    - **password**: Current password for verification

    Requires valid JWT token in Authorization header

    Note: If this is an admin user, the alert recipient email will also be updated
    """
    # Verify password
    if not verify_password(email_data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect"
        )

    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == email_data.new_email,
        User.id != current_user.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use by another user"
        )

    # Store old email for alert recipient update
    old_email = current_user.email

    # Update email
    current_user.email = email_data.new_email
    db.commit()

    # If admin user, update or create alert recipient
    recipient_action = None
    if current_user.is_admin:
        from app.core.models import AlertRecipient

        # Find existing recipient with old email
        recipient = db.query(AlertRecipient).filter(
            AlertRecipient.email == old_email
        ).first()

        if recipient:
            # Update existing recipient
            recipient.email = email_data.new_email
            db.commit()
            recipient_action = "updated"
        else:
            # Create new recipient if none exists
            new_recipient = AlertRecipient(email=email_data.new_email)
            db.add(new_recipient)
            db.commit()
            recipient_action = "created"

    # Build appropriate success message
    if recipient_action:
        message = f"Email changed successfully and alert recipient {recipient_action}"
    else:
        message = "Email changed successfully"

    return MessageResponse(message=message)
