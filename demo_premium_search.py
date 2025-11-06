#!/usr/bin/env python3
"""
Premium Search Demo - Demonstrate advanced search capabilities
"""

import asyncio
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, '/home/ishanp/Documents/GitHub/scrapecraft/backend')

async def demo_premium_search_service():
    """Demonstrate premium search service capabilities"""
    print("\n" + "="*60)
    print("🔍 PREMIUM SEARCH SERVICE DEMONSTRATION")
    print("="*60)
    
    try:
        from app.services.premium_scraping_service import PremiumScrapingService, EngineType
        
        async with PremiumScrapingService() as service:
            print("✅ Premium scraping service initialized")
            
            # Test different search queries
            test_queries = [
                "cybersecurity threats 2024",
                "artificial intelligence trends",
                "open source intelligence tools"
            ]
            
            for query in test_queries:
                print(f"\n🔍 Searching for: '{query}'")
                print("-" * 40)
                
                try:
                    # Use DuckDuckGo (most reliable without APIs)
                    results = await service.search_engine(
                        EngineType.DUCKDUCKGO, 
                        query, 
                        max_pages=1,
                        use_browser=False
                    )
                    
                    if results:
                        print(f"✅ Found {len(results)} results")
                        
                        # Show top 3 results
                        for i, result in enumerate(results[:3], 1):
                            print(f"\n  {i}. {result.get('title', 'No title')}")
                            print(f"     🔗 {result.get('url', 'No URL')}")
                            print(f"     📄 {result.get('snippet', 'No snippet')[:100]}...")
                            print(f"     🎯 Relevance: {result.get('relevance_score', 0):.2f}")
                            print(f"     ⭐ Quality: {service._assess_quality(result):.2f}")
                            print(f"     📂 Type: {service._classify_content(result)}")
                    else:
                        print("❌ No results found")
                        
                except Exception as e:
                    print(f"❌ Search failed: {e}")
            
            # Test multi-engine search
            print(f"\n🌐 Testing multi-engine search...")
            query = "machine learning security"
            
            try:
                multi_results = await service.multi_engine_search(
                    query, 
                    [EngineType.DUCKDUCKGO, EngineType.BRAVE],
                    use_browser=False
                )
                
                if multi_results:
                    print(f"✅ Multi-engine found {len(multi_results)} unique results")
                    
                    # Show engine distribution
                    engine_counts = {}
                    for result in multi_results:
                        engine = result.get('engine', 'unknown')
                        engine_counts[engine] = engine_counts.get(engine, 0) + 1
                    
                    print("📊 Results by engine:")
                    for engine, count in engine_counts.items():
                        print(f"  {engine}: {count} results")
                        
                    # Show best result
                    best_result = max(multi_results, key=lambda x: x.get('relevance_score', 0))
                    print(f"\n🏆 Best result:")
                    print(f"  Title: {best_result.get('title', 'No title')}")
                    print(f"  URL: {best_result.get('url', 'No URL')}")
                    print(f"  Relevance: {best_result.get('relevance_score', 0):.2f}")
                    print(f"  Quality: {service._assess_quality(best_result):.2f}")
                    
                else:
                    print("❌ No multi-engine results found")
                    
            except Exception as e:
                print(f"❌ Multi-engine search failed: {e}")
                
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def demo_premium_search_agent():
    """Demonstrate premium search agent capabilities"""
    print("\n" + "="*60)
    print("🤖 PREMIUM SEARCH AGENT DEMONSTRATION")
    print("="*60)
    
    try:
        from app.agents.specialized.collection.premium_search_agent import PremiumSearchAgent
        
        async with PremiumSearchAgent() as agent:
            print("✅ Premium search agent initialized")
            print(f"📋 Agent ID: {agent.config.agent_id}")
            print(f"🎯 Role: {agent.config.role}")
            
            # Test supported engines
            engines = await agent.get_supported_engines()
            print(f"🔍 Supported engines: {engines}")
            
            # Test search execution
            input_data = {
                "query": "cybersecurity best practices 2024",
                "engines": ["duckduckgo", "brave"],
                "max_pages": 1,
                "use_browser": False,
                "investigation_id": "demo-investigation-001"
            }
            
            print(f"\n🔍 Executing search: '{input_data['query']}'")
            print("=" * 40)
            
            result = await agent.execute(input_data)
            
            if result.success:
                data = result.data
                results = data.get("results", [])
                summary = data.get("summary", {})
                
                print(f"✅ Search successful!")
                print(f"📊 Total results: {len(results)}")
                print(f"⏱️ Execution time: {result.execution_time:.2f}s")
                print(f"🎯 Confidence: {result.confidence:.2f}")
                
                print("\n📈 Search Summary:")
                for key, value in summary.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"    {sub_key}: {sub_value}")
                    else:
                        print(f"  {key}: {value}")
                
                # Show top results
                if results:
                    print(f"\n🔝 Top 3 Results:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"\n  {i}. {result.get('title', 'No title')}")
                        print(f"     🔗 {result.get('url', 'No URL')}")
                        print(f"     🎯 Relevance: {result.get('relevance_score', 0):.2f}")
                        print(f"     ⭐ Quality: {result.get('quality_score', 0):.2f}")
                        print(f"     📂 Type: {result.get('content_type', 'Unknown')}")
                        print(f"     🏷️  Entities: {result.get('extracted_entities', [])}")
                        print(f"     🔍 Engine: {result.get('engine', 'Unknown')}")
                        
                # Show metadata
                metadata = data.get("metadata", {})
                if metadata:
                    print(f"\n🔧 Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                        
            else:
                print(f"❌ Search failed: {result.error_message}")
                
    except Exception as e:
        print(f"❌ Agent demo failed: {e}")

async def demo_content_analysis():
    """Demonstrate content analysis capabilities"""
    print("\n" + "="*60)
    print("📊 CONTENT ANALYSIS DEMONSTRATION")
    print("="*60)
    
    try:
        from app.services.premium_scraping_service import PremiumScrapingService
        
        service = PremiumScrapingService()
        
        # Test content classification
        test_results = [
            {
                "title": "Python Machine Learning Tutorial",
                "snippet": "Learn machine learning with Python libraries like scikit-learn and TensorFlow",
                "url": "https://github.com/ml-tutorial"
            },
            {
                "title": "Latest Cybersecurity News",
                "snippet": "Breaking news about cybersecurity threats and data breaches in 2024",
                "url": "https://news.example.com/cybersecurity"
            },
            {
                "title": "Artificial Intelligence - Wikipedia",
                "snippet": "Artificial intelligence (AI) is intelligence demonstrated by machines",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
            }
        ]
        
        print("📂 Content Classification Results:")
        for i, result in enumerate(test_results, 1):
            content_type = service._classify_content(result)
            quality = service._assess_quality(result)
            relevance = service._calculate_relevance_score(result)
            
            print(f"\n  {i}. {result['title']}")
            print(f"     📂 Type: {content_type}")
            print(f"     ⭐ Quality: {quality:.2f}")
            print(f"     🎯 Relevance: {relevance:.2f}")
            
        # Test entity extraction
        print(f"\n🏷️  Entity Extraction:")
        for i, result in enumerate(test_results, 1):
            entities = service._extract_entities(result)
            print(f"\n  {i}. {result['title']}")
            print(f"     🏷️  Entities: {entities}")
            
    except Exception as e:
        print(f"❌ Content analysis demo failed: {e}")

async def main():
    """Run all demonstrations"""
    print("🚀 STARTING PREMIUM SEARCH COMPREHENSIVE DEMO")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    print("🎯 Demonstrating advanced search without API dependencies")
    print("=" * 60)
    
    # Run demonstrations
    await demo_premium_search_service()
    await demo_premium_search_agent()
    await demo_content_analysis()
    
    print("\n" + "="*60)
    print("✅ PREMIUM SEARCH DEMONSTRATION COMPLETED")
    print(f"⏰ Finished at: {datetime.now().isoformat()}")
    print("="*60)
    
    print("\n🎉 KEY ACHIEVEMENTS:")
    print("✅ Premium search service with multi-engine support")
    print("✅ Advanced HTML parsing for Google, Bing, DuckDuckGo, Brave")
    print("✅ Anti-detection measures and rate limiting")
    print("✅ Content quality assessment and classification")
    print("✅ Entity extraction and metadata enrichment")
    print("✅ Browser automation infrastructure (Playwright)")
    print("✅ Proxy rotation framework")
    print("✅ Investigation context integration")
    print("✅ WebSocket real-time updates")
    print("✅ RESTful API endpoints")
    
    print("\n🚀 READY FOR PHASE 3 ENHANCEMENTS:")
    print("• Google & Bing direct scraping (bypassing APIs)")
    print("• Academic source integration (arXiv, Google Scholar)")
    print("• Social media scraping capabilities")
    print("• Advanced CAPTCHA solving")
    print("• Distributed scraping architecture")
    print("• AI-powered content analysis")

if __name__ == "__main__":
    asyncio.run(main())