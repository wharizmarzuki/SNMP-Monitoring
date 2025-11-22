"""
Diagnostic script to check if you have enough data for reports.
Run this to see what data exists in your database.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.core import models

def check_report_data():
    """Check if sufficient data exists for generating reports."""

    db = next(get_db())

    print("=" * 70)
    print("REPORT DATA DIAGNOSTIC")
    print("=" * 70)

    # Check if database tables exist
    try:
        device_count = db.query(models.Device).count()
    except Exception as e:
        if "no such table" in str(e).lower():
            print("\n❌ DATABASE NOT INITIALIZED")
            print("   The database exists but has no tables!")
            print("\n💡 SOLUTION:")
            print("   1. Start the backend service:")
            print("      cd backend")
            print("      python -m app.main")
            print("\n   2. This will automatically create all database tables")
            print("   3. Then run this diagnostic script again")
            print("\n" + "=" * 70)
            return
        else:
            raise

    print(f"\n📱 DEVICES:")
    print(f"   Total devices: {device_count}")

    if device_count == 0:
        print("   ❌ NO DEVICES FOUND - You need to discover devices first!")
        print("      Run device discovery from the UI")
        return

    # Show devices
    devices = db.query(models.Device).all()
    for device in devices:
        print(f"   - {device.hostname} ({device.ip_address}) - Reachable: {device.is_reachable}")

    # Check device_metrics
    print(f"\n📊 DEVICE METRICS (CPU/Memory/Uptime):")
    device_metrics_count = db.query(models.DeviceMetric).count()
    print(f"   Total records: {device_metrics_count}")

    if device_metrics_count == 0:
        print("   ❌ NO DEVICE METRICS - Polling hasn't run yet!")
        print("      Start the polling service and wait for at least 1 poll cycle")
    else:
        # Get date range
        oldest = db.query(models.DeviceMetric).order_by(models.DeviceMetric.timestamp.asc()).first()
        newest = db.query(models.DeviceMetric).order_by(models.DeviceMetric.timestamp.desc()).first()
        print(f"   Oldest metric: {oldest.timestamp}")
        print(f"   Newest metric: {newest.timestamp}")
        print(f"   ✅ Data available for reports!")

        # Sample data
        sample = db.query(models.DeviceMetric).first()
        print(f"   Sample: CPU={sample.cpu_utilization}%, Memory={sample.memory_utilization}%, Uptime={sample.uptime_seconds}s")

    # Check interface_metrics
    print(f"\n🌐 INTERFACE METRICS (Bandwidth/Packet Drops):")
    interface_count = db.query(models.Interface).count()
    interface_metrics_count = db.query(models.InterfaceMetric).count()
    print(f"   Total interfaces: {interface_count}")
    print(f"   Total metric records: {interface_metrics_count}")

    if interface_metrics_count == 0:
        print("   ❌ NO INTERFACE METRICS - Polling hasn't collected interface data!")
    else:
        oldest = db.query(models.InterfaceMetric).order_by(models.InterfaceMetric.timestamp.asc()).first()
        newest = db.query(models.InterfaceMetric).order_by(models.InterfaceMetric.timestamp.desc()).first()
        print(f"   Oldest metric: {oldest.timestamp}")
        print(f"   Newest metric: {newest.timestamp}")
        print(f"   ✅ Data available for bandwidth reports!")

        # Check for packet drops
        drops = db.query(models.InterfaceMetric).filter(
            (models.InterfaceMetric.discards_in > 0) | (models.InterfaceMetric.discards_out > 0)
        ).count()
        print(f"   Records with packet drops: {drops}")
        if drops == 0:
            print("   ℹ️  No packet drops detected (this is normal/good)")

    # Suggest date ranges
    print(f"\n📅 SUGGESTED DATE RANGES FOR REPORTS:")
    if device_metrics_count > 0:
        oldest = db.query(models.DeviceMetric).order_by(models.DeviceMetric.timestamp.asc()).first()
        newest = db.query(models.DeviceMetric).order_by(models.DeviceMetric.timestamp.desc()).first()

        print(f"   Start Date: {oldest.timestamp.strftime('%Y-%m-%d')}")
        print(f"   End Date:   {newest.timestamp.strftime('%Y-%m-%d')}")
        print(f"\n   💡 Use these dates in the report page to see your data!")
    else:
        print("   ❌ No data available yet - start polling first!")

    # Check polling frequency
    if device_metrics_count > 1:
        print(f"\n⏱️  POLLING FREQUENCY:")
        recent_metrics = db.query(models.DeviceMetric).order_by(
            models.DeviceMetric.timestamp.desc()
        ).limit(2).all()

        if len(recent_metrics) == 2:
            time_diff = recent_metrics[0].timestamp - recent_metrics[1].timestamp
            print(f"   Last poll interval: {time_diff}")
            print(f"   Total data points: {device_metrics_count}")

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)

    if device_count == 0:
        print("❌ No devices - Run discovery first")
    elif device_metrics_count == 0:
        print("❌ No metrics - Start polling service")
    elif interface_metrics_count == 0:
        print("⚠️  Devices polled but no interface data - Check polling configuration")
    else:
        print("✅ You have data! Generate reports with the suggested date range above.")

    print("=" * 70)

if __name__ == "__main__":
    check_report_data()
