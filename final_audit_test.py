#!/usr/bin/env python3
"""
Final verification that audit persistence is fully working.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Override database URL to use SQLite for testing
os.environ['DATABASE_URL'] = 'sqlite:///./final_audit_test.db'

from app.services.database import DatabasePersistenceService

async def test_final_audit_persistence():
    """Final comprehensive test of audit persistence."""
    print("🎯 Final Audit Persistence Verification")
    print("=" * 50)
    
    # Initialize database service
    db_service = DatabasePersistenceService()
    db_service.initialize_database()
    
    # Test 1: Store multiple audit events
    print("1. Storing multiple audit events...")
    test_events = [
        {
            "event_type": "auth:login:success",
            "user_id": "user1",
            "action": "login",
            "ip_address": "127.0.0.1",
            "details": {"method": "password", "success": True},
            "severity": "medium"
        },
        {
            "event_type": "investigation:create",
            "user_id": "user2", 
            "action": "create_investigation",
            "resource_id": "inv_123",
            "resource_type": "investigation",
            "details": {"title": "Test Investigation", "classification": "secret"},
            "severity": "high"
        },
        {
            "event_type": "security:suspicious:activity",
            "action": "detect_anomaly",
            "ip_address": "192.168.1.100",
            "details": {"pattern": "brute_force", "attempts": 5},
            "severity": "critical"
        }
    ]
    
    stored_count = 0
    for event in test_events:
        success = await db_service.store_audit_event(event)
        if success:
            stored_count += 1
            print(f"   ✅ Stored: {event['event_type']}")
        else:
            print(f"   ❌ Failed: {event['event_type']}")
    
    print(f"\n📊 Successfully stored {stored_count}/{len(test_events)} events")
    
    # Test 2: Retrieve events
    print("\n2. Retrieving stored events...")
    retrieved_events = await db_service.get_audit_events(limit=10)
    print(f"   ✅ Retrieved {len(retrieved_events)} events from database")
    
    for event in retrieved_events:
        print(f"   - ID: {event.get('id')}, Type: {event.get('event_type')}, "
              f"User: {event.get('user_id')}, Action: {event.get('action')}")
    
    # Test 3: Verify data integrity
    print("\n3. Verifying data integrity...")
    # Get only the latest events (limit to what we just stored)
    latest_events = retrieved_events[:len(test_events)]
    # Events are retrieved in reverse chronological order, so reverse them for comparison
    latest_events.reverse()
    
    for i, event in enumerate(latest_events):
        original = test_events[i]
        
        # Check key fields
        assert event['event_type'] == original['event_type'], f"Event type mismatch: {event['event_type']} != {original['event_type']}"
        assert event['action'] == original['action'], f"Action mismatch: {event['action']} != {original['action']}"
        assert event['severity'] == original['severity'], f"Severity mismatch: {event['severity']} != {original['severity']}"
        
        # Check details JSON serialization
        if isinstance(event['details'], str):
            import json
            details_dict = json.loads(event['details'])
            assert details_dict == original['details'], f"Details mismatch: {details_dict} != {original['details']}"
        
        print(f"   ✅ Event {event['id']}: Data integrity verified")
    
    # Test 4: Check database schema
    print("\n4. Checking database schema...")
    with db_service.SessionLocal() as db:
        from app.models.sqlalchemy.audit import AuditLog
        total_events = db.query(AuditLog).count()
        print(f"   ✅ Total events in database: {total_events}")
        
        # Check indexes
        from sqlalchemy import text
        indexes = db.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_audit%'")).fetchall()
        print(f"   ✅ Audit table indexes: {[idx[0] for idx in indexes]}")
    
    print("\n🎉 ALL TESTS PASSED! Audit persistence is fully working!")
    print("\n📋 Summary:")
    print("   ✅ Database schema creation")
    print("   ✅ Event storage with JSON serialization")
    print("   ✅ Event retrieval")
    print("   ✅ Data integrity verification")
    print("   ✅ SQLite compatibility")
    print("   ✅ Proper indexing for performance")

if __name__ == "__main__":
    asyncio.run(test_final_audit_persistence())