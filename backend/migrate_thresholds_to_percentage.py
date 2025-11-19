"""
Database Migration: Convert Interface Thresholds to Percentage-Based

This script resets all interface packet_drop_threshold values to 0.1%
(the new default percentage-based threshold).

Background:
- Old system: Thresholds were absolute packet drop counts (e.g., 100 drops)
- New system: Thresholds are percentages of total traffic (e.g., 0.1%)

This is a breaking change that requires resetting all thresholds because:
1. Old values (100) are meaningless as percentages (would mean 100%)
2. Converting old values to equivalent percentages is impractical
3. Default of 0.1% is a sensible starting point for most interfaces

Run this script once after deploying the percentage-based threshold code.

Usage:
    python backend/migrate_thresholds_to_percentage.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.app.core.database import SessionLocal


def migrate_thresholds():
    """Reset all interface thresholds to 0.1% (new default)"""
    db = SessionLocal()
    try:
        # Count existing interfaces
        count_result = db.execute(text("SELECT COUNT(*) FROM interface_metrics"))
        total_interfaces = count_result.scalar()

        print(f"Found {total_interfaces} interface records")
        print("Resetting all packet_drop_threshold values to 0.1% (new percentage-based default)...")

        # Update all thresholds to 0.1
        result = db.execute(
            text("UPDATE interface_metrics SET packet_drop_threshold = 0.1")
        )
        db.commit()

        print(f"✅ Successfully updated {result.rowcount} interface thresholds to 0.1%")
        print("\nNext steps:")
        print("1. Users should review and adjust thresholds based on their requirements")
        print("2. Recommended thresholds:")
        print("   - 0.01% for critical links")
        print("   - 0.1% for normal operations (default)")
        print("   - 1.0% for noisy environments")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Interface Threshold Migration: Absolute → Percentage")
    print("=" * 60)
    print()

    response = input("This will reset ALL interface thresholds to 0.1%. Continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        migrate_thresholds()
    else:
        print("Migration cancelled.")
