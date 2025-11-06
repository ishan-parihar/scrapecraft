#!/usr/bin/env python3
"""
Frontend Workflow Analysis Report

This script analyzes the frontend Investigation Planner workflow issues
without requiring a running backend server. Based on code analysis,
it identifies the root causes and provides specific fixes.
"""

import json
from datetime import datetime

def analyze_workflow_issues():
    """Analyze the workflow issues based on code examination"""
    
    print("🔍 ScrapeCraft Frontend Workflow Analysis")
    print("=" * 60)
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "workflow_issues": [],
        "root_causes": [],
        "specific_fixes": [],
        "frontend_backend_mismatches": []
    }
    
    print("📋 ISSUE ANALYSIS")
    print("-" * 30)
    
    # Issue 1: WebSocket Endpoint Mismatch
    print("\n1. WebSocket Endpoint Mismatch")
    issue = {
        "component": "WebSocket Connection",
        "issue": "Frontend connects to wrong WebSocket endpoint",
        "details": {
            "frontend_expects": "/ws/{investigationId}",
            "backend_provides": "/api/osint/ws/{investigation_id}",
            "problem": "URL structure mismatch causing connection failures"
        }
    }
    analysis["workflow_issues"].append(issue)
    print(f"   ❌ Frontend expects: /ws/{{investigationId}}")
    print(f"   ✅ Backend provides: /api/osint/ws/{{investigation_id}}")
    
    # Issue 2: Missing WebSocket Broadcasting
    print("\n2. Missing WebSocket Broadcasting in AI Investigation Service")
    issue = {
        "component": "AI Investigation Service",
        "issue": "No real-time progress updates via WebSocket",
        "details": {
            "service": "app/services/ai_investigation.py",
            "problem": "Background tasks run silently without broadcasting status changes"
        }
    }
    analysis["workflow_issues"].append(issue)
    print(f"   ❌ Background tasks don't broadcast WebSocket messages")
    print(f"   ❌ No phase transition notifications")
    print(f"   ❌ No agent assignment updates")
    
    # Issue 3: Investigation System Disconnection
    print("\n3. AI and OSINT Investigation Systems Not Integrated")
    issue = {
        "component": "Investigation Management",
        "issue": "AI investigations don't create OSINT records",
        "details": {
            "ai_system": "/api/ai-investigation/*",
            "osint_system": "/api/osint/investigations/*",
            "problem": "Separate systems don't share data"
        }
    }
    analysis["workflow_issues"].append(issue)
    print(f"   ❌ AI investigations don't create OSINT investigation records")
    print(f"   ❌ No agent assignments in AI investigations")
    print(f"   ❌ Frontend can't find agents for AI investigations")
    
    # Issue 4: Frontend Investigation ID Mismatch
    print("\n4. Frontend Investigation ID Mismatch")
    issue = {
        "component": "InvestigationPlanner.tsx",
        "issue": "Uses wrong investigation ID for WebSocket connection",
        "details": {
            "api_response": "response.data.investigation_id",
            "websocket_uses": "investigationId from props",
            "problem": "Different IDs cause WebSocket connection to wrong channel"
        }
    }
    analysis["workflow_issues"].append(issue)
    print(f"   ❌ API returns new investigation_id")
    print(f"   ❌ WebSocket uses props.investigationId")
    print(f"   ❌ Mismatch prevents real-time updates")
    
    print("\n🎯 ROOT CAUSES")
    print("-" * 30)
    
    # Root Cause 1
    cause = {
        "cause": "Separate Development of AI and OSINT Systems",
        "impact": "No integration between investigation types",
        "components": ["AI Investigation API", "OSINT API", "Agent Management"]
    }
    analysis["root_causes"].append(cause)
    print(f"1. Separate AI and OSINT investigation systems developed independently")
    
    # Root Cause 2
    cause = {
        "cause": "Missing Real-time Communication Architecture",
        "impact": "No progress updates reach frontend",
        "components": ["WebSocket Broadcasting", "Background Task Communication"]
    }
    analysis["root_causes"].append(cause)
    print(f"2. No real-time communication from background tasks to frontend")
    
    # Root Cause 3
    cause = {
        "cause": "Frontend State Management Not Updated for AI Investigations",
        "impact": "Frontend can't handle AI investigation responses",
        "components": ["InvestigationPlanner", "WebSocket Store", "Agent Coordinator"]
    }
    analysis["root_causes"].append(cause)
    print(f"3. Frontend components not adapted for AI investigation workflow")
    
    print("\n🔧 SPECIFIC FIXES REQUIRED")
    print("-" * 30)
    
    # Fix 1: WebSocket Broadcasting
    fix = {
        "file": "app/services/ai_investigation.py",
        "change": "Add WebSocket broadcasting to investigation progress",
        "code": """
# Add to ai_investigation.py
from app.services.enhanced_websocket import enhanced_manager

# After each phase transition:
await enhanced_manager.broadcast(
    f"investigation_{investigation_id}",
    {
        "type": "investigation:updated",
        "investigation_id": investigation_id,
        "status": investigation["status"],
        "current_phase": investigation["current_phase"],
        "progress_percentage": investigation["progress_percentage"]
    }
)
        """
    }
    analysis["specific_fixes"].append(fix)
    print(f"1. Add WebSocket broadcasting to AI investigation service")
    
    # Fix 2: Frontend WebSocket URL
    fix = {
        "file": "frontend/src/store/websocketStore.ts",
        "change": "Update WebSocket URL to match backend",
        "code": "// Change from: /ws/${investigationId}\n// To: /api/osint/ws/${investigationId}"
    }
    analysis["specific_fixes"].append(fix)
    print(f"2. Fix frontend WebSocket URL")
    
    # Fix 3: Investigation Integration
    fix = {
        "file": "app/services/ai_investigation.py",
        "change": "Create OSINT investigation records for AI investigations",
        "code": """
# When starting AI investigation, also create OSINT record:
osint_investigation = await osint_service.create_investigation({
    "title": f"AI: {request.target}",
    "objective": request.objective,
    "status": "active",
    "priority": request.priority,
    "ai_investigation_id": investigation_id
})
        """
    }
    analysis["specific_fixes"].append(fix)
    print(f"3. Integrate AI investigations with OSINT system")
    
    # Fix 4: Agent Assignment
    fix = {
        "file": "app/services/ai_investigation.py",
        "change": "Assign agents when AI investigation starts",
        "code": """
# Auto-assign collection agents:
agents = await agent_service.assign_agents_to_investigation(
    investigation_id, 
    ["social_media_collector", "surface_web_collector", "public_records_collector"]
)
        """
    }
    analysis["specific_fixes"].append(fix)
    print(f"4. Auto-assign agents to AI investigations")
    
    # Fix 5: Frontend Investigation ID Handling
    fix = {
        "file": "frontend/src/components/OSINT/Chat/InvestigationPlanner.tsx",
        "change": "Use correct investigation ID for WebSocket connection",
        "code": "// Use response.data.investigation_id instead of props.investigationId"
    }
    analysis["specific_fixes"].append(fix)
    print(f"5. Fix frontend investigation ID handling")
    
    print("\n🔄 FRONTEND-BACKEND MISMATCHES")
    print("-" * 30)
    
    mismatch = {
        "component": "WebSocket Endpoints",
        "frontend": "/ws/{investigationId}",
        "backend": "/api/osint/ws/{investigation_id}",
        "fix": "Update frontend to use backend endpoint"
    }
    analysis["frontend_backend_mismatches"].append(mismatch)
    print(f"1. WebSocket URLs don't match")
    
    mismatch = {
        "component": "Investigation APIs",
        "frontend": "Uses /ai-investigation/start but expects OSINT features",
        "backend": "AI and OSINT systems are separate",
        "fix": "Integrate the two systems or create unified API"
    }
    analysis["frontend_backend_mismatches"].append(mismatch)
    print(f"2. Investigation systems are disconnected")
    
    mismatch = {
        "component": "Agent Management",
        "frontend": "Expects agents via /osint/investigations/{id}/agents",
        "backend": "AI investigations don't create OSINT records",
        "fix": "Create OSINT records for AI investigations"
    }
    analysis["frontend_backend_mismatches"].append(mismatch)
    print(f"3. Agent endpoints don't work with AI investigations")
    
    # Save analysis
    with open("frontend_workflow_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n📄 Detailed analysis saved to: frontend_workflow_analysis.json")
    
    print("\n📊 SUMMARY")
    print("=" * 60)
    print(f"Total Issues Found: {len(analysis['workflow_issues'])}")
    print(f"Root Causes: {len(analysis['root_causes'])}")
    print(f"Specific Fixes Required: {len(analysis['specific_fixes'])}")
    print(f"Frontend-Backend Mismatches: {len(analysis['frontend_backend_mismatches'])}")
    
    print(f"\n💡 PRIORITY FIXES:")
    print("1. Add WebSocket broadcasting to AI investigation service")
    print("2. Fix frontend WebSocket URL to match backend")
    print("3. Create OSINT investigation records for AI investigations")
    print("4. Auto-assign agents when AI investigations start")
    print("5. Fix frontend investigation ID handling in WebSocket connection")
    
    return analysis

if __name__ == "__main__":
    analyze_workflow_issues()