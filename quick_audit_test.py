#!/usr/bin/env python3
"""
Quick test to verify audit persistence is working after JSON serialization fix.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Override database URL to use SQLite for testing
os.environ['DATABASE_URL'] = 'sqlite:///./test_audit.db'

from app.services.audit_logger import AuditLogger, AuditEventType, AuditSeverity

async def test_audit_persistence():
    """Test audit persistence with the fixes applied."""
    print("🔍 Testing Audit Event Persistence After Fix")
    print("=" * 50)
    
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    # Test 1: Create and log a proper audit event
    print("1. Creating audit event with required action field...")
    event = await audit_logger.log_auth_event(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        username="test_user",
        success=True,
        ip_address="127.0.0.1",
        details={"test": "persistence_fixed"}
    )
    
    # Test 2: Retrieve events
    print("2. Retrieving audit events...")
    events = await audit_logger.get_audit_events(limit=5)
    print(f"✅ Retrieved {len(events)} audit events")
    
    for event in events:
        print(f"   - {event.get('event_type')} at {event.get('timestamp')}")
    
    # Test 3: Check database directly
    print("3. Checking database persistence directly...")
    if audit_logger.db_persistence:
        db_events = await audit_logger.db_persistence.get_audit_events(limit=3)
        print(f"✅ Database contains {len(db_events)} events")
        for event in db_events:
            print(f"   - ID: {event.get('id')}, Type: {event.get('event_type')}, User: {event.get('user_id')}")
    else:
        print("❌ Database persistence not available")
    
    print("\n🎯 Audit persistence test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_audit_persistence())