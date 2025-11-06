#!/usr/bin/env python3
"""
Simple test script to start the backend and test WebSocket connectivity.
"""

import subprocess
import time
import asyncio
import httpx
import websockets
import json
import signal
import sys

# Process tracking
backend_process = None

def signal_handler(sig, frame):
    """Clean shutdown on Ctrl+C"""
    print('\nShutting down...')
    if backend_process:
        backend_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def test_backend():
    """Test backend connectivity and WebSocket"""
    print("🔍 Testing backend connectivity...")
    
    # Test HTTP endpoints
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            health_resp = await client.get('http://127.0.0.1:8000/health', timeout=5.0)
            print(f"✅ Health check: {health_resp.status_code}")
            print(f"   Response: {health_resp.text[:200]}...")
            
            # Test OSINT investigations endpoint
            inv_resp = await client.get('http://127.0.0.1:8000/api/osint/investigations', timeout=5.0)
            print(f"✅ OSINT investigations: {inv_resp.status_code}")
            
            # Test AI investigation endpoint
            start_resp = await client.post('http://127.0.0.1:8000/api/ai-investigation/start', 
                                         json={'target': 'test target', 'objective': 'test objective', 'priority': 'medium'}, 
                                         timeout=10.0)
            print(f"✅ AI Investigation start: {start_resp.status_code}")
            if start_resp.status_code == 200:
                response_data = start_resp.json()
                investigation_id = response_data.get('investigation_id')
                print(f"   Started investigation: {investigation_id}")
                
                # Test WebSocket connection
                print("\n🔌 Testing WebSocket connection...")
                try:
                    ws_url = f"ws://127.0.0.1:8000/api/osint/ws/{investigation_id}"
                    async with websockets.connect(ws_url) as websocket:
                        print(f"✅ Connected to WebSocket: {ws_url}")
                        
                        # Send a test message
                        test_message = {
                            "type": "investigation_command",
                            "message": "Test investigation command",
                            "investigation_id": investigation_id
                        }
                        await websocket.send(json.dumps(test_message))
                        print(f"📤 Sent: {test_message}")
                        
                        # Wait for response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            response_data = json.loads(response)
                            print(f"📥 Received: {response_data}")
                        except asyncio.TimeoutError:
                            print("⚠️  No response received within 5 seconds")
                        
                except Exception as ws_error:
                    print(f"❌ WebSocket error: {ws_error}")
            else:
                print(f"❌ AI Investigation start failed: {start_resp.text[:200]}")
                
        except Exception as e:
            print(f"❌ Backend connection error: {e}")
            return False
    
    return True

def main():
    print("🚀 Starting ScrapeCraft Backend Test")
    print("=" * 50)
    
    # Start the backend server
    print("🔧 Starting backend server...")
    try:
        backend_process = subprocess.Popen([
            '/home/ishanp/Documents/GitHub/scrapecraft/backend/venv/bin/python',
            '-m', 'uvicorn', 'app.main:app',
            '--host', '127.0.0.1',
            '--port', '8000',
            '--reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Test the backend
        success = asyncio.run(test_backend())
        
        if success:
            print("\n✅ All tests passed! Server is running correctly.")
            print("📚 API Documentation: http://127.0.0.1:8000/docs")
            print("🔌 WebSocket endpoint: ws://127.0.0.1:8000/api/osint/ws/{investigation_id}")
            print("\n📝 Frontend should now be able to connect successfully.")
            print("💡 The backend is running in the background.")
            print("🛑 Press Ctrl+C to stop the server.")
            
            # Keep server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Tests failed!")
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
    finally:
        if backend_process:
            print("\n🛑 Stopping backend server...")
            backend_process.terminate()
            backend_process.wait()

if __name__ == "__main__":
    main()