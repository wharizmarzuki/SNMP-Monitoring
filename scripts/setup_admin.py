#!/usr/bin/env python3
"""
Admin User Setup Script

This script creates the initial admin user for the SNMP Monitoring System.
It should be run during first deployment or when no users exist in the system.

The script will:
1. Check if any users already exist
2. Prompt for username, password, and email
3. Validate inputs
4. Create the admin user
5. Add the email as an alert recipient
"""
import sys
import os
import re
import getpass
from pathlib import Path

# Add backend to path
# Use resolve() to convert relative path to absolute path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Change working directory to backend to ensure database is created there
os.chdir(str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.models import User, AlertRecipient, Base
from app.core.security import get_password_hash


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format

    Rules:
    - 3-50 characters
    - Alphanumeric, underscore, hyphen only
    - Must start with letter
    """
    if not username:
        return False, "Username cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must be at most 50 characters"

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return False, "Username must start with a letter and contain only letters, numbers, underscore, or hyphen"

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Rules:
    - At least 6 characters
    - Recommended: mix of letters, numbers, special characters
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    # Optional: Check for stronger password
    has_letter = re.search(r'[a-zA-Z]', password)
    has_number = re.search(r'\d', password)

    if not (has_letter and has_number):
        print("⚠️  Warning: Password should contain both letters and numbers for better security")

    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format
    """
    if not email:
        return False, "Email cannot be empty"

    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    return True, ""


def get_user_input() -> tuple[str, str, str]:
    """
    Prompt user for admin credentials

    Returns:
        tuple: (username, password, email)
    """
    print("\n" + "="*60)
    print("🔐 SNMP Monitoring System - Admin Setup")
    print("="*60)
    print("\nThis wizard will create the initial admin user for your system.")
    print("The email address will be used for receiving alert notifications.\n")

    # Get username
    while True:
        username = input("Enter admin username: ").strip()
        valid, error = validate_username(username)
        if valid:
            break
        print(f"❌ {error}")

    # Get password
    while True:
        password = getpass.getpass("Enter admin password: ")
        valid, error = validate_password(password)
        if not valid:
            print(f"❌ {error}")
            continue

        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match")
            continue

        break

    # Get email
    while True:
        email = input("Enter admin email (for alerts): ").strip()
        valid, error = validate_email(email)
        if valid:
            break
        print(f"❌ {error}")

    return username, password, email


def create_admin_user(db: Session, username: str, password: str, email: str) -> bool:
    """
    Create admin user in database

    Args:
        db: Database session
        username: Admin username
        password: Plain text password (will be hashed)
        email: Admin email

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print(f"❌ Error: User with username '{username}' or email '{email}' already exists")
            return False

        # Create user
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Admin user '{username}' created successfully (ID: {admin_user.id})")
        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False


def add_alert_recipient(db: Session, email: str) -> bool:
    """
    Add admin email as alert recipient

    Args:
        db: Database session
        email: Admin email

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if recipient already exists
        existing = db.query(AlertRecipient).filter(
            AlertRecipient.email == email
        ).first()

        if existing:
            print(f"ℹ️  Email '{email}' is already configured as alert recipient")
            return True

        # Add recipient
        recipient = AlertRecipient(email=email)
        db.add(recipient)
        db.commit()

        print(f"✅ Email '{email}' added as alert recipient")
        return True

    except Exception as e:
        print(f"❌ Error adding alert recipient: {e}")
        db.rollback()
        return False


def main():
    """Main setup function"""
    print("\n🚀 Starting SNMP Monitoring System Setup...\n")

    # Create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready\n")

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if any users exist
        user_count = db.query(User).count()

        if user_count > 0:
            print(f"⚠️  Warning: {user_count} user(s) already exist in the database")
            response = input("Do you want to create another admin user? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n❌ Setup cancelled")
                return 1

        # Get user input
        username, password, email = get_user_input()

        # Confirm
        print("\n" + "-"*60)
        print("📝 Please confirm the details:")
        print(f"   Username: {username}")
        print(f"   Email:    {email}")
        print("-"*60)
        confirm = input("\nCreate admin user with these details? (yes/no): ").strip().lower()

        if confirm not in ['yes', 'y']:
            print("\n❌ Setup cancelled")
            return 1

        print("\n⏳ Creating admin user...")

        # Create admin user
        if not create_admin_user(db, username, password, email):
            return 1

        # Add alert recipient
        if not add_alert_recipient(db, email):
            print("⚠️  Warning: User created but failed to add alert recipient")
            print("   You can add the email manually in the Settings page")

        print("\n" + "="*60)
        print("🎉 Setup completed successfully!")
        print("="*60)
        print(f"\n✅ Admin user '{username}' is ready")
        print(f"✅ Alert notifications will be sent to: {email}")
        print("\nYou can now:")
        print("  1. Start the backend server: cd backend && uvicorn main:app")
        print("  2. Start the frontend: cd frontend && npm run dev")
        print("  3. Login at http://localhost:3000/login")
        print("\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
