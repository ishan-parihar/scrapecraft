#!/usr/bin/env python3
"""
Frontend-to-Backend Workflow Test for ScrapeCraft Investigation Planner

This test simulates the complete user journey:
1. Starting an investigation from the frontend
2. WebSocket connection attempts
3. Real-time updates and agent status
4. Task progress and completion

Run this test to identify why the UI shows "Investigation started" but then nothing happens.
"""

import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendBackendTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000"
        self.investigation_id = None
        self.ws_messages = []
        self.api_responses = {}
    
    async def test_api_start_investigation(self) -> Dict[str, Any]:
        """Test Step 1: Start investigation via API (like frontend does)"""
        logger.info("🚀 Step 1: Starting investigation via API...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # This is what the frontend InvestigationPlanner.tsx sends
                payload = {
                    "target": "Research the activism in Delhi NCR regarding air pollution against the government",
                    "objective": "plan investigation",
                    "priority": "medium"
                }
                
                logger.info(f"📤 Sending POST request to {self.backend_url}/ai-investigation/start")
                logger.info(f"📦 Payload: {json.dumps(payload, indent=2)}")
                
                async with session.post(f"{self.backend_url}/ai-investigation/start", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.api_responses['start'] = data
                        self.investigation_id = data.get('investigation_id')
                        
                        logger.info(f"✅ Investigation started successfully!")
                        logger.info(f"📋 Investigation ID: {self.investigation_id}")
                        logger.info(f"📄 Response: {json.dumps(data, indent=2)}")
                        
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to start investigation: {response.status}")
                        logger.error(f"📄 Error response: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"❌ Exception starting investigation: {e}")
            return {"error": str(e)}
    
    async def test_websocket_connection(self) -> bool:
        """Test Step 2: WebSocket connection (like frontend does)"""
        logger.info("🔌 Step 2: Testing WebSocket connection...")
        
        if not self.investigation_id:
            logger.error("❌ No investigation ID available for WebSocket test")
            return False
        
        # Test both potential WebSocket URLs
        ws_urls_to_test = [
            f"{self.ws_url}/ws/{self.investigation_id}",  # Frontend expects this
            f"{self.ws_url}/api/osint/ws/{self.investigation_id}",  # Backend provides this
        ]
        
        for i, ws_url in enumerate(ws_urls_to_test, 1):
            logger.info(f"🌐 Testing WebSocket URL {i}: {ws_url}")
            
            try:
                async with websockets.connect(ws_url, timeout=5) as websocket:
                    logger.info(f"✅ WebSocket connected successfully to: {ws_url}")
                    
                    # Send a test message
                    test_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                    await websocket.send(json.dumps(test_message))
                    logger.info(f"📤 Sent test message: {test_message}")
                    
                    # Wait for response (with timeout)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        logger.info(f"📥 Received WebSocket response: {response}")
                        
                        # Store the working WebSocket URL
                        self.working_ws_url = ws_url
                        return True
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"⚠️  No response from WebSocket within 3 seconds")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Failed to connect to {ws_url}: {e}")
                continue
        
        logger.error("❌ All WebSocket connection attempts failed")
        return False
    
    async def test_investigation_status(self) -> Dict[str, Any]:
        """Test Step 3: Check investigation status (like frontend polling)"""
        logger.info("📊 Step 3: Testing investigation status polling...")
        
        if not self.investigation_id:
            logger.error("❌ No investigation ID available for status check")
            return {"error": "No investigation ID"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # This is what the frontend polls for
                status_url = f"{self.backend_url}/ai-investigation/{self.investigation_id}/status"
                logger.info(f"📈 Checking status at: {status_url}")
                
                async with session.get(status_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.api_responses['status'] = data
                        
                        logger.info(f"✅ Status check successful!")
                        logger.info(f"📊 Status response: {json.dumps(data, indent=2)}")
                        
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to get status: {response.status}")
                        logger.error(f"📄 Error response: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            logger.error(f"❌ Exception checking status: {e}")
            return {"error": str(e)}
    
    async def test_active_investigations(self) -> List[Dict[str, Any]]:
        """Test Step 4: Check active investigations"""
        logger.info("🔍 Step 4: Testing active investigations endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/ai-investigation/active") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.api_responses['active'] = data
                        
                        logger.info(f"✅ Active investigations retrieved!")
                        logger.info(f"📋 Found {len(data)} active investigations")
                        
                        for i, inv in enumerate(data, 1):
                            logger.info(f"   {i}. {inv.get('investigation_id')}: {inv.get('status')} - {inv.get('target', 'No target')}")
                        
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to get active investigations: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Exception checking active investigations: {e}")
            return []
    
    async def test_websocket_monitoring(self, duration: int = 10) -> List[Dict[str, Any]]:
        """Test Step 5: Monitor WebSocket messages over time"""
        logger.info(f"📡 Step 5: Monitoring WebSocket messages for {duration} seconds...")
        
        if not self.investigation_id:
            logger.error("❌ No investigation ID available for monitoring")
            return []
        
        messages = []
        
        try:
            # Use the working WebSocket URL if we found one, otherwise try both
            ws_url = getattr(self, 'working_ws_url', f"{self.ws_url}/api/osint/ws/{self.investigation_id}")
            
            async with websockets.connect(ws_url, timeout=5) as websocket:
                logger.info(f"📡 Connected to {ws_url} for monitoring")
                
                # Send a subscription message if needed
                subscribe_msg = {
                    "type": "subscribe",
                    "investigation_id": self.investigation_id,
                    "events": ["status", "agent", "task", "evidence"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                logger.info(f"📤 Sent subscription message")
                
                # Monitor for specified duration
                start_time = datetime.now()
                while (datetime.now() - start_time).total_seconds() < duration:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        parsed = json.loads(message)
                        parsed['received_at'] = datetime.now().isoformat()
                        messages.append(parsed)
                        
                        logger.info(f"📥 WebSocket message received: {json.dumps(parsed, indent=2)}")
                        
                    except asyncio.TimeoutError:
                        # No message received in this interval, continue
                        continue
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️  Failed to parse WebSocket message: {e}")
                        continue
                
                logger.info(f"📊 Monitoring complete. Received {len(messages)} messages")
                return messages
                
        except Exception as e:
            logger.error(f"❌ Exception during WebSocket monitoring: {e}")
            return []
    
    async def analyze_results(self) -> Dict[str, Any]:
        """Analyze all test results and identify issues"""
        logger.info("🔍 Step 6: Analyzing results...")
        
        analysis = {
            "issues_found": [],
            "working_components": [],
            "recommendations": []
        }
        
        # Check API start response
        if 'start' in self.api_responses:
            start_data = self.api_responses['start']
            if 'investigation_id' in start_data:
                analysis["working_components"].append("✅ API: Start Investigation")
            else:
                analysis["issues_found"].append("❌ API start missing investigation_id")
        else:
            analysis["issues_found"].append("❌ API start failed")
        
        # Check WebSocket connection
        if hasattr(self, 'working_ws_url'):
            analysis["working_components"].append("✅ WebSocket: Connection Established")
            analysis["recommendations"].append("🔧 Update frontend WebSocket URL to match backend")
        else:
            analysis["issues_found"].append("❌ WebSocket connection failed")
        
        # Check status polling
        if 'status' in self.api_responses:
            status_data = self.api_responses['status']
            if status_data.get('status') in ['running', 'initializing', 'completed']:
                analysis["working_components"].append("✅ API: Status Polling")
            else:
                analysis["issues_found"].append(f"❌ Unexpected investigation status: {status_data.get('status')}")
        else:
            analysis["issues_found"].append("❌ Status polling failed")
        
        # Check active investigations
        if 'active' in self.api_responses:
            active_data = self.api_responses['active']
            if self.investigation_id in [inv.get('investigation_id') for inv in active_data]:
                analysis["working_components"].append("✅ API: Active Investigations")
            else:
                analysis["issues_found"].append("❌ Investigation not found in active list")
        
        # Generate specific recommendations
        if "❌ WebSocket connection failed" in analysis["issues_found"]:
            analysis["recommendations"].append("🔧 Fix WebSocket endpoint mismatch between frontend and backend")
            analysis["recommendations"].append("🔧 Update frontend to use /api/osint/ws/{investigation_id}")
        
        if len(self.ws_messages) == 0:
            analysis["issues_found"].append("❌ No WebSocket messages received")
            analysis["recommendations"].append("🔧 Add WebSocket broadcasting in AI investigation service")
        
        return analysis
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete frontend-to-backend workflow test"""
        logger.info("🧪 Starting Complete Frontend-to-Backend Workflow Test")
        logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "analysis": {}
        }
        
        # Step 1: Start investigation
        results["steps"]["start"] = await self.test_api_start_investigation()
        await asyncio.sleep(1)
        
        # Step 2: Test WebSocket connection
        results["steps"]["websocket"] = await self.test_websocket_connection()
        await asyncio.sleep(1)
        
        # Step 3: Check investigation status
        results["steps"]["status"] = await self.test_investigation_status()
        await asyncio.sleep(1)
        
        # Step 4: Check active investigations
        results["steps"]["active"] = await self.test_active_investigations()
        await asyncio.sleep(1)
        
        # Step 5: Monitor WebSocket messages
        results["steps"]["websocket_messages"] = await self.test_websocket_monitoring(duration=10)
        self.ws_messages = results["steps"]["websocket_messages"]
        
        # Step 6: Analyze results
        results["analysis"] = await self.analyze_results()
        
        # Print summary
        self.print_test_summary(results)
        
        return results
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print a comprehensive test summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        analysis = results["analysis"]
        
        logger.info(f"🔍 Investigation ID: {self.investigation_id}")
        logger.info(f"📡 WebSocket Messages: {len(self.ws_messages)}")
        
        if analysis["working_components"]:
            logger.info("\n✅ WORKING COMPONENTS:")
            for component in analysis["working_components"]:
                logger.info(f"   {component}")
        
        if analysis["issues_found"]:
            logger.info("\n❌ ISSUES FOUND:")
            for issue in analysis["issues_found"]:
                logger.info(f"   {issue}")
        
        if analysis["recommendations"]:
            logger.info("\n🔧 RECOMMENDATIONS:")
            for rec in analysis["recommendations"]:
                logger.info(f"   {rec}")
        
        # Overall assessment
        total_issues = len(analysis["issues_found"])
        if total_issues == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Frontend-to-backend workflow is working correctly.")
        elif total_issues <= 2:
            logger.info(f"\n⚠️  {total_issues} issue(s) found. Workflow needs minor fixes.")
        else:
            logger.info(f"\n❌ {total_issues} issues found. Workflow needs significant fixes.")

async def main():
    """Main test runner"""
    logger.info("🚀 ScrapeCraft Frontend-to-Backend Workflow Test")
    logger.info("This test simulates the complete user journey in the Investigation Planner")
    
    tester = FrontendBackendTest()
    
    try:
        results = await tester.run_complete_test()
        
        # Save results to file
        with open("/home/ishanp/Documents/GitHub/scrapecraft/backend/frontend_workflow_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("\n📄 Full test results saved to: frontend_workflow_test_results.json")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        return None
    except Exception as e:
        logger.error(f"\n💥 Test failed with exception: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())