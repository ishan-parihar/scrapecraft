#!/usr/bin/env python3
"""
Minimal backend test
"""
import subprocess
import time
import sys

print("🚀 Starting minimal backend test...")

# Start server
try:
    process = subprocess.Popen([
        '/home/ishanp/Documents/GitHub/scrapecraft/backend/venv/bin/python',
        '-m', 'uvicorn', 'app.main:app',
        '--host', '127.0.0.1',
        '--port', '8000'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    print("⏳ Server starting...")
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is None:
        print("✅ Server process is running")
        print("📚 Testing connection...")
        
        # Simple connection test
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = s.connect_ex(('127.0.0.1', 8000))
            s.close()
            if result == 0:
                print("✅ Port 8000 is accessible")
            else:
                print("❌ Port 8000 is not accessible")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        # Show some server output
        print("\n📋 Server output:")
        for i, line in enumerate(process.stdout):
            if i < 10:  # Show first 10 lines
                print(f"   {line.strip()}")
            else:
                break
        
        print("\n✅ Server is running. Press Ctrl+C to stop.")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
    else:
        print("❌ Server failed to start")
        print("Output:")
        print(process.stdout.read())
        
except Exception as e:
    print(f"❌ Error: {e}")