#!/usr/bin/env python3
"""
Quick backend server test with real-time output
"""

import subprocess
import time
import sys
import os
import threading

def start_server_with_output():
    """Start server and show output in real-time"""
    print("🚀 Starting ScrapeCraft Backend Server...")
    
    # Start the backend server
    process = subprocess.Popen([
        '/home/ishanp/Documents/GitHub/scrapecraft/backend/venv/bin/python',
        '-m', 'uvicorn', 'app.main:app',
        '--host', '127.0.0.1',
        '--port', '8000',
        '--log-level', 'info'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    def read_output():
        """Read and print server output"""
        for line in iter(process.stdout.readline, ''):
            print(f"[SERVER] {line.strip()}")
    
    # Start reading output in background
    output_thread = threading.Thread(target=read_output)
    output_thread.daemon = True
    output_thread.start()
    
    # Wait a bit for startup
    time.sleep(8)
    
    # Test connection
    print("\n🔍 Testing connection...")
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        if result == 0:
            print("✅ Port 8000 is accessible!")
            
            # Test HTTP request
            import httpx
            try:
                resp = httpx.get('http://127.0.0.1:8000/health', timeout=5.0)
                print(f"✅ HTTP Request successful: {resp.status_code}")
                print(f"Response: {resp.text[:200]}...")
            except Exception as e:
                print(f"❌ HTTP Request failed: {e}")
        else:
            print(f"❌ Port 8000 not accessible (code: {result})")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    print("\n🛑 Press Ctrl+C to stop the server...")
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    start_server_with_output()