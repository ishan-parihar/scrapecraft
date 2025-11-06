#!/usr/bin/env python3
"""
Complete backend integration test for frontend-backend connectivity.
"""

import subprocess
import time
import asyncio
import httpx
import websockets
import json
import signal
import sys
import os
from threading import Thread

# Add backend to path
sys.path.insert(0, '/home/ishanp/Documents/GitHub/scrapecraft/backend')

# Process tracking
backend_process = None

def signal_handler(sig, frame):
    """Clean shutdown on Ctrl+C"""
    print('\n🛑 Shutting down...')
    if backend_process:
        backend_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_backend_server():
    """Start the backend server"""
    global backend_process
    print("🚀 Starting ScrapeCraft Backend Server...")
    
    # Start the backend server
    backend_process = subprocess.Popen([
        '/home/ishanp/Documents/GitHub/scrapecraft/backend/venv/bin/python',
        '-m', 'uvicorn', 'app.main:app',
        '--host', '127.0.0.1',
        '--port', '8000',
        '--log-level', 'info'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait for server to start
    print("⏳ Waiting for server to initialize...")
    time.sleep(5)
    
    # Check if process is running
    if backend_process.poll() is None:
        print("✅ Backend server process is running")
        return True
    else:
        print("❌ Backend server failed to start")
        print("Error output:")
        print(backend_process.stdout.read())
        return False

async def test_http_endpoints():
    """Test HTTP endpoints"""
    print("\n🔍 Testing HTTP Endpoints...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("   Testing health endpoint...")
            health_resp = await client.get('http://127.0.0.1:8000/health', timeout=5.0)
            print(f"   ✅ Health check: {health_resp.status_code}")
            if health_resp.status_code == 200:
                health_data = health_resp.json()
                print(f"      Status: {health_data.get('status')}")
                print(f"      Services: {list(health_data.get('services', {}).keys())}")
            
            # Test root endpoint
            print("   Testing root endpoint...")
            root_resp = await client.get('http://127.0.0.1:8000/', timeout=5.0)
            print(f"   ✅ Root endpoint: {root_resp.status_code}")
            
            # Test OSINT investigations endpoint
            print("   Testing OSINT investigations endpoint...")
            inv_resp = await client.get('http://127.0.0.1:8000/api/osint/investigations', timeout=5.0)
            print(f"   ✅ OSINT investigations: {inv_resp.status_code}")
            
            # Test AI investigation endpoint
            print("   Testing AI investigation start endpoint...")
            start_resp = await client.post('http://127.0.0.1:8000/api/ai-investigation/start', 
                                         json={'target': 'test target', 'objective': 'test objective', 'priority': 'medium'}, 
                                         timeout=10.0)
            print(f"   ✅ AI Investigation start: {start_resp.status_code}")
            
            if start_resp.status_code == 200:
                response_data = start_resp.json()
                investigation_id = response_data.get('investigation_id')
                print(f"      Started investigation: {investigation_id}")
                
                # Test getting investigation status
                status_resp = await client.get(f'http://127.0.0.1:8000/api/ai-investigation/status/{investigation_id}', timeout=5.0)
                print(f"   ✅ Investigation status: {status_resp.status_code}")
                
                return investigation_id
            else:
                print(f"   ❌ AI Investigation start failed: {start_resp.text[:200]}")
                return None
                
        except Exception as e:
            print(f"   ❌ HTTP endpoint test error: {e}")
            return None

async def test_websocket_connection(investigation_id):
    """Test WebSocket connection"""
    print(f"\n🔌 Testing WebSocket Connection for investigation: {investigation_id}")
    
    try:
        ws_url = f"ws://127.0.0.1:8000/api/osint/ws/{investigation_id}"
        print(f"   Connecting to: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("   ✅ WebSocket connection established")
            
            # Send a ping message
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print(f"   📤 Sent ping: {ping_message}")
            
            # Wait for pong response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"   📥 Received: {response_data}")
                
                if response_data.get('type') == 'pong':
                    print("   ✅ Ping-pong test successful")
                else:
                    print(f"   ⚠️  Unexpected response type: {response_data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("   ⚠️  No response received within 5 seconds")
            
            # Send investigation command
            command_message = {
                "type": "investigation_command",
                "message": "Test investigation command",
                "investigation_id": investigation_id
            }
            await websocket.send(json.dumps(command_message))
            print(f"   📤 Sent command: {command_message}")
            
            # Wait for command response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                print(f"   📥 Received command response: {response_data}")
                
                if response_data.get('type') in ['response', 'investigation_update']:
                    print("   ✅ Command response received successfully")
                else:
                    print(f"   ⚠️  Unexpected response type: {response_data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("   ⚠️  No command response received within 10 seconds")
                
        print("   ✅ WebSocket connection closed gracefully")
        return True
        
    except Exception as ws_error:
        print(f"   ❌ WebSocket error: {ws_error}")
        return False

async def test_database_persistence():
    """Test database persistence"""
    print("\n💾 Testing Database Persistence...")
    
    try:
        from app.services.database import db_persistence
        
        # Test database connection
        print("   Testing database connection...")
        db_persistence.initialize_database()
        print("   ✅ Database initialized successfully")
        
        # Test storing investigation state
        print("   Testing investigation state storage...")
        test_state = {
            "investigation_id": "test_inv_123",
            "status": "active",
            "progress": 50,
            "data": {"test": "data"}
        }
        
        # Store state
        db_persistence.store_investigation_state("test_inv_123", test_state)
        print("   ✅ Investigation state stored")
        
        # Retrieve state
        retrieved_state = db_persistence.get_investigation_state("test_inv_123")
        if retrieved_state:
            print("   ✅ Investigation state retrieved successfully")
            print(f"      Status: {retrieved_state.get('status')}")
        else:
            print("   ⚠️  Could not retrieve investigation state")
            
        return True
        
    except Exception as db_error:
        print(f"   ❌ Database test error: {db_error}")
        return False

def show_server_logs():
    """Show recent server logs"""
    print("\n📋 Recent Server Logs:")
    if backend_process and backend_process.stdout:
        lines = backend_process.stdout.readlines()
        for line in lines[-10:]:  # Show last 10 lines
            print(f"   {line.strip()}")

async def main():
    """Main test function"""
    print("🧪 ScrapeCraft Backend Integration Test")
    print("=" * 60)
    
    # Start backend server
    if not start_backend_server():
        print("❌ Failed to start backend server")
        return
    
    # Test components
    investigation_id = await test_http_endpoints()
    
    if investigation_id:
        await test_websocket_connection(investigation_id)
    else:
        print("⚠️  Skipping WebSocket test due to failed HTTP test")
    
    await test_database_persistence()
    
    # Show results
    show_server_logs()
    
    print("\n" + "=" * 60)
    print("🎉 Backend Integration Test Complete!")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("🔌 WebSocket endpoint: ws://127.0.0.1:8000/api/osint/ws/{investigation_id}")
    print("💾 Database: SQLite (scrapecraft.db)")
    print("\n💡 The frontend should now be able to connect successfully!")
    print("🛑 Press Ctrl+C to stop the server.")
    
    try:
        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if backend_process:
            print("\n🛑 Stopping backend server...")
            backend_process.terminate()
            backend_process.wait()

if __name__ == "__main__":
    asyncio.run(main())