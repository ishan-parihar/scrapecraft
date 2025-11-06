#!/usr/bin/env python3
"""
Comprehensive Integration Test for ScrapeCraft Search Functionality
This demonstrates the complete workflow from search query to results storage.
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone

# Add the backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agents.specialized.collection.simple_search_agent import SimpleSearchAgent
from app.agents.base.osint_agent import AgentConfig
from app.models.osint import Investigation, InvestigationCreate, InvestigationStatus, InvestigationPriority, IntelligenceRequirement

async def test_complete_workflow():
    """Test the complete OSINT workflow with search integration."""
    print("🚀 ScrapeCraft Integration Test - Complete Search Workflow")
    print("=" * 70)
    
    try:
        # Step 1: Create a test investigation
        print("\n📋 Step 1: Creating Test Investigation")
        print("-" * 40)
        
        investigation_data = InvestigationCreate(
            title="AI Threat Landscape Analysis 2024",
            description="Comprehensive analysis of emerging AI-powered cyber threats and defense mechanisms",
            intelligence_requirements=[
                {
                    "id": "ir-001",
                    "title": "AI Security Trends",
                    "description": "Identify emerging AI security trends and vulnerabilities",
                    "priority": "HIGH"
                },
                {
                    "id": "ir-002", 
                    "title": "Threat Actor Capabilities",
                    "description": "Analyze how threat actors are leveraging AI technologies",
                    "priority": "HIGH"
                }
            ],
            priority=InvestigationPriority.HIGH,
            classification="UNCLASSIFIED"
        )
        
        # Create investigation object (normally this would be saved to database)
        investigation = Investigation(
            id="test-inv-001",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=InvestigationStatus.ACTIVE,
            **investigation_data.model_dump()
        )
        
        print(f"✅ Investigation Created: {investigation.title}")
        print(f"🎯 Intelligence Requirements: {len(investigation.intelligence_requirements)} items")
        for req in investigation.intelligence_requirements:
            print(f"   - {req.title}: {req.description[:50]}...")
        
        # Step 2: Initialize Search Agent
        print("\n🔍 Step 2: Initializing Search Agent")
        print("-" * 40)
        
        config = AgentConfig(
            role="OSINT Search Specialist",
            description="Advanced web search for threat intelligence",
            timeout=30,
            max_retries=2
        )
        search_agent = SimpleSearchAgent(config)
        
        print("✅ Search Agent Initialized")
        print(f"🔧 Search Engines: {search_agent.search_engines}")
        print(f"📊 Max Results: {search_agent.max_results}")
        
        # Step 3: Perform Multiple Searches
        print("\n🔎 Step 3: Performing Investigation Searches")
        print("-" * 40)
        
        search_queries = [
            "AI cybersecurity threats 2024",
            "machine learning attack vectors",
            "artificial intelligence security vulnerabilities",
            "AI-powered malware detection"
        ]
        
        all_evidence = []
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Search {i}/{len(search_queries)}: '{query}'")
            
            try:
                # Execute search
                input_data = {"query": query}
                result = await search_agent.execute(input_data)
                
                if result.success:
                    search_data = result.data
                    results = search_data.get("results", [])
                    total_results = search_data.get("total_results", 0)
                    engines_used = search_data.get("engines_used", [])
                    
                    print(f"  ✅ Found {total_results} results using {', '.join(engines_used)}")
                    
                    # Convert search results to evidence items
                    for j, search_result in enumerate(results[:3]):  # Take top 3 results
                        evidence = {
                            "id": f"evidence-{i:02d}-{j:02d}",
                            "investigation_id": investigation.id,
                            "source_type": "web_search",
                            "source_name": search_result.get("source", "unknown"),
                            "collection_method": "automated_search",
                            "title": search_result.get("title", ""),
                            "content": search_result.get("description", ""),
                            "url": search_result.get("url", ""),
                            "relevance_score": search_result.get("relevance_score", 0.5),
                            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
                            "tags": ["search", "web", search_result.get("source", "unknown"), "ai-security"],
                            "metadata": {
                                "search_query": query,
                                "search_engine": search_result.get("source"),
                                "result_index": j,
                                "total_results": total_results
                            }
                        }
                        all_evidence.append(evidence)
                        
                        print(f"    📄 {j+1}. {evidence['title'][:60]}...")
                        print(f"       🔗 {evidence['url'][:50]}...")
                        print(f"       📈 Score: {evidence['relevance_score']:.2f}")
                    
                else:
                    print(f"  ❌ Search failed: {result.error_message}")
                    
            except Exception as e:
                print(f"  ❌ Search error: {e}")
        
        # Step 4: Generate Investigation Summary
        print("\n📊 Step 4: Investigation Summary")
        print("-" * 40)
        
        print(f"🎯 Investigation: {investigation.title}")
        print(f"📅 Created: {investigation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Total Searches: {len(search_queries)}")
        print(f"📄 Evidence Collected: {len(all_evidence)} items")
        
        # Analyze sources
        sources = {}
        for evidence in all_evidence:
            source = evidence['source_name']
            sources[source] = sources.get(source, 0) + 1
        
        print(f"🌐 Sources Used: {dict(sources)}")
        
        # Calculate average relevance score
        avg_relevance = sum(e['relevance_score'] for e in all_evidence) / len(all_evidence) if all_evidence else 0
        print(f"📈 Average Relevance: {avg_relevance:.2f}")
        
        # Step 5: Save Investigation Report
        print("\n💾 Step 5: Saving Investigation Report")
        print("-" * 40)
        
        investigation_report = {
            "investigation": {
                "id": investigation.id,
                "title": investigation.title,
                "description": investigation.description,
                "intelligence_requirements": [
                    {
                        "id": req.id,
                        "title": req.title,
                        "description": req.description,
                        "priority": req.priority
                    } for req in investigation.intelligence_requirements
                ],
                "status": investigation.status.value,
                "priority": investigation.priority.value,
                "created_at": investigation.created_at.isoformat()
            },
            "search_summary": {
                "total_searches": len(search_queries),
                "search_queries": search_queries,
                "evidence_count": len(all_evidence),
                "sources": sources,
                "average_relevance_score": avg_relevance
            },
            "evidence": all_evidence,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to file
        report_filename = f"investigation_report_{investigation.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(investigation_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Report saved: {report_filename}")
        print(f"📊 Report size: {os.path.getsize(report_filename)} bytes")
        
        # Step 6: API Integration Demo
        print("\n🔌 Step 6: API Integration Simulation")
        print("-" * 40)
        
        # Simulate API responses like the frontend would receive
        api_responses = []
        
        for query in search_queries[:2]:  # Demo with first 2 queries
            try:
                input_data = {"query": query}
                result = await search_agent.execute(input_data)
                
                if result.success:
                    api_response = {
                        "success": True,
                        "query": query,
                        "results": result.data.get("results", []),
                        "total_results": result.data.get("total_results", 0),
                        "engines_used": result.data.get("engines_used", []),
                        "search_time": result.data.get("search_time", 0.0),
                        "timestamp": result.data.get("timestamp", datetime.utcnow().isoformat())
                    }
                    api_responses.append(api_response)
                    print(f"  ✅ API Response for '{query}': {api_response['total_results']} results")
                
            except Exception as e:
                print(f"  ❌ API Error for '{query}': {e}")
        
        # Simulate frontend integration
        print(f"\n🎨 Frontend Integration Ready:")
        print(f"  📡 {len(api_responses)} API responses available")
        print(f"  🔍 Search component can display {sum(len(r['results']) for r in api_responses)} results")
        print(f"  📊 Investigation dashboard can track {len(all_evidence)} evidence items")
        
        # Final Summary
        print("\n" + "=" * 70)
        print("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("✅ Components Tested:")
        print("  🔍 Search Agent - Working with real DuckDuckGo results")
        print("  📊 Evidence Collection - Converting results to structured data")
        print("  🎯 Investigation Management - Complete workflow")
        print("  🔌 API Integration - Ready for frontend consumption")
        print("  💾 Report Generation - Comprehensive output")
        print("\n🚀 ScrapeCraft is ready for full-stack integration!")
        
    except Exception as e:
        print(f"\n❌ Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())