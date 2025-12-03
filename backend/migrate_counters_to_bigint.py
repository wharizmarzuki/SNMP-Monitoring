#!/usr/bin/env python3
"""
Migration script to convert InterfaceMetric counter columns from Float to BigInteger.

This script:
1. Backs up the interface_metrics table
2. Creates a new table with BigInteger columns
3. Migrates data from old table to new table
4. Replaces the old table with the new one

Usage:
    python migrate_counters_to_bigint.py
"""

import sqlite3
import os
import shutil
from datetime import datetime

# Database path (adjust if needed)
DB_PATH = os.path.join(os.path.dirname(__file__), "snmp_monitoring.db")
BACKUP_PATH = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def backup_database():
    """Create a backup of the database before migration."""
    print(f"Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("✓ Backup created successfully")

def migrate_counters():
    """Migrate counter columns from Float to BigInteger."""
    print("\nConnecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(interface_metrics)")
        columns = cursor.fetchall()

        # Check if octets_in is already INTEGER type
        octets_in_type = next((col[2] for col in columns if col[1] == 'octets_in'), None)

        if octets_in_type and octets_in_type.upper() in ('INTEGER', 'BIGINT'):
            print("✓ Migration already applied - counters are already BigInteger")
            return

        print("Starting migration...")

        # Step 1: Create new table with BigInteger columns
        print("  1. Creating new table schema...")
        cursor.execute("""
            CREATE TABLE interface_metrics_new (
                id INTEGER PRIMARY KEY,
                interface_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                admin_status INTEGER,
                oper_status INTEGER,
                octets_in INTEGER,
                octets_out INTEGER,
                errors_in INTEGER,
                errors_out INTEGER,
                discards_in INTEGER,
                discards_out INTEGER,
                FOREIGN KEY(interface_id) REFERENCES interfaces(id)
            )
        """)
        print("  ✓ New table created")

        # Step 2: Copy data from old table to new table
        print("  2. Migrating data...")
        cursor.execute("""
            INSERT INTO interface_metrics_new
            SELECT
                id,
                interface_id,
                timestamp,
                admin_status,
                oper_status,
                CAST(octets_in AS INTEGER),
                CAST(octets_out AS INTEGER),
                CAST(errors_in AS INTEGER),
                CAST(errors_out AS INTEGER),
                CAST(discards_in AS INTEGER),
                CAST(discards_out AS INTEGER)
            FROM interface_metrics
        """)
        rows_migrated = cursor.rowcount
        print(f"  ✓ Migrated {rows_migrated} rows")

        # Step 3: Drop old table
        print("  3. Dropping old table...")
        cursor.execute("DROP TABLE interface_metrics")
        print("  ✓ Old table dropped")

        # Step 4: Rename new table
        print("  4. Renaming new table...")
        cursor.execute("ALTER TABLE interface_metrics_new RENAME TO interface_metrics")
        print("  ✓ Table renamed")

        # Step 5: Recreate indexes (if any existed)
        print("  5. Recreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_interface_metrics_interface_id
            ON interface_metrics(interface_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_interface_metrics_timestamp
            ON interface_metrics(timestamp)
        """)
        print("  ✓ Indexes created")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"   - {rows_migrated} rows migrated")
        print(f"   - Backup saved to: {BACKUP_PATH}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"   Database has been rolled back")
        print(f"   You can restore from backup: {BACKUP_PATH}")
        raise
    finally:
        conn.close()

def main():
    """Main migration function."""
    print("=" * 60)
    print("SNMP Monitoring - Counter Type Migration")
    print("Float → BigInteger")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("   Please ensure the database path is correct")
        return

    # Create backup
    backup_database()

    # Run migration
    migrate_counters()

    print("\n" + "=" * 60)
    print("Migration complete! You can now restart the application.")
    print("=" * 60)

if __name__ == "__main__":
    main()
