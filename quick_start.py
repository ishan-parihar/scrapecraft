#!/usr/bin/env python3
"""
ScrapeGraph Enhanced - Quick Start Script
Run this script to quickly test the enhanced scraping service.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.services.enhanced_scraping_service import EnhancedScrapingService

async def quick_start_demo():
    """Demonstrate the enhanced scraping service capabilities."""
    
    print("🚀 ScrapeGraph Enhanced - Quick Start Demo")
    print("=" * 50)
    
    # Initialize the service
    service = EnhancedScrapingService()
    
    try:
        # Test 1: Basic scraping
        print("\n1. Basic Web Scraping")
        print("-" * 30)
        
        urls = ["https://example.com"]
        results = await service.execute_pipeline(
            urls=urls,
            schema=None,
            prompt="Extract the main title and content"
        )
        
        for result in results:
            if result['success']:
                data = result['data']
                print(f"✅ URL: {result['url']}")
                print(f"   Title: {data.get('title', 'N/A')}")
                print(f"   Content: {data.get('content', 'N/A')[:100]}...")
                print(f"   Status Code: {data.get('metadata', {}).get('status_code', 'N/A')}")
            else:
                print(f"❌ Error: {result['error']}")
        
        # Test 2: Structured extraction
        print("\n2. Structured Data Extraction")
        print("-" * 30)
        
        schema = {
            "website_title": {"description": "The main title of the website"},
            "main_content": {"description": "The main content or description"},
            "contact_email": {"description": "Any email address found on the page"}
        }
        
        urls = ["https://python.org"]
        results = await service.execute_pipeline(
            urls=urls,
            schema=schema,
            prompt="Extract website information"
        )
        
        for result in results:
            if result['success']:
                data = result['data']
                print(f"✅ URL: {result['url']}")
                print(f"   Website Title: {data.get('website_title', 'N/A')}")
                print(f"   Main Content: {data.get('main_content', 'N/A')[:100]}...")
                print(f"   Contact Email: {data.get('contact_email', 'N/A')}")
                print(f"   Links Found: {data.get('metadata', {}).get('link_count', 0)}")
            else:
                print(f"❌ Error: {result['error']}")
        
        # Test 3: Search functionality
        print("\n3. Search URLs")
        print("-" * 30)
        
        search_results = await service.search_urls("python programming", 3)
        print(f"✅ Search Query: 'python programming'")
        print(f"   Results Found: {len(search_results)}")
        
        for i, result in enumerate(search_results, 1):
            print(f"   {i}. {result['description']}")
            print(f"      URL: {result['url']}")
        
        # Test 4: Batch processing
        print("\n4. Batch Processing")
        print("-" * 30)
        
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://python.org"
        ]
        
        results = await service.execute_pipeline(
            urls=urls,
            schema={
                "title": {"description": "Page title"},
                "content_summary": {"description": "Brief content summary"}
            },
            prompt="Extract page information"
        )
        
        successful = sum(1 for r in results if r['success'])
        print(f"✅ Processed {len(urls)} URLs")
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(urls) - successful}")
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['url']}")
            if result['success']:
                data = result['data']
                print(f"      Title: {data.get('title', 'N/A')[:50]}...")
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Start the API server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Check the user guide: SCRAPEGRAPH_USER_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.http_client.aclose()

if __name__ == "__main__":
    print("Starting ScrapeGraph Enhanced demo...")
    print("Make sure you have an internet connection for this demo.")
    asyncio.run(quick_start_demo())