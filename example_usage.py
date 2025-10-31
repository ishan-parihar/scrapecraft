#!/usr/bin/env python3
"""
Example usage scripts for ScrapeGraph Enhanced API
Demonstrates various ways to use the scraping service.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def example_1_basic_scraping():
    """Example 1: Basic web scraping"""
    print("🔍 Example 1: Basic Web Scraping")
    print("-" * 40)
    
    # Start scraping job
    payload = {
        "urls": ["https://example.com"],
        "prompt": "Extract the main title and description"
    }
    
    response = requests.post(f"{BASE_URL}/api/scraping/execute", json=payload)
    task_data = response.json()
    
    print(f"Task started: {task_data['task_id']}")
    print(f"Status: {task_data['status']}")
    
    # Wait for completion and get results
    task_id = task_data['task_id']
    for _ in range(10):  # Max 10 attempts
        response = requests.get(f"{BASE_URL}/api/scraping/status/{task_id}")
        status_data = response.json()
        
        if status_data['status'] == 'completed':
            response = requests.get(f"{BASE_URL}/api/scraping/results/{task_id}")
            results = response.json()
            
            for result in results:
                if result['success']:
                    data = result['data']
                    print(f"✅ Title: {data.get('title', 'N/A')}")
                    print(f"✅ Content: {data.get('content', 'N/A')[:100]}...")
                else:
                    print(f"❌ Error: {result['error']}")
            break
        elif status_data['status'] == 'failed':
            print(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
            break
        
        time.sleep(1)
    
    print()

def example_2_structured_extraction():
    """Example 2: Structured data extraction"""
    print("🏗️ Example 2: Structured Data Extraction")
    print("-" * 40)
    
    payload = {
        "urls": ["https://python.org"],
        "prompt": "Extract website information including title, content, and any contact details",
        "schema": {
            "website_title": {"description": "The main title of the website"},
            "main_content": {"description": "The main content or description"},
            "contact_email": {"description": "Any email address found on the page"},
            "phone_number": {"description": "Any phone number found on the page"}
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/scraping/execute", json=payload)
    task_id = response.json()['task_id']
    
    # Wait for completion
    while True:
        status_response = requests.get(f"{BASE_URL}/api/scraping/status/{task_id}")
        status = status_response.json()['status']
        
        if status in ['completed', 'failed']:
            break
        time.sleep(0.5)
    
    # Get results
    results_response = requests.get(f"{BASE_URL}/api/scraping/results/{task_id}")
    results = results_response.json()
    
    for result in results:
        if result['success']:
            data = result['data']
            print(f"✅ URL: {result['url']}")
            print(f"   Website Title: {data.get('website_title', 'N/A')}")
            print(f"   Main Content: {data.get('main_content', 'N/A')[:100]}...")
            print(f"   Contact Email: {data.get('contact_email', 'N/A')}")
            print(f"   Phone Number: {data.get('phone_number', 'N/A')}")
            print(f"   Links Found: {data.get('metadata', {}).get('link_count', 0)}")
        else:
            print(f"❌ Error: {result['error']}")
    
    print()

def example_3_batch_processing():
    """Example 3: Batch processing multiple URLs"""
    print("📦 Example 3: Batch Processing")
    print("-" * 40)
    
    payload = {
        "urls": [
            "https://example.com",
            "https://python.org",
            "https://httpbin.org/html"
        ],
        "prompt": "Extract page information and metadata",
        "schema": {
            "page_title": {"description": "The title of the page"},
            "content_summary": {"description": "Brief summary of the content"},
            "external_links": {"description": "Number of external links"}
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/scraping/execute", json=payload)
    task_id = response.json()['task_id']
    
    # Wait for completion
    while True:
        status_response = requests.get(f"{BASE_URL}/api/scraping/status/{task_id}")
        status = status_response.json()['status']
        
        if status in ['completed', 'failed']:
            break
        time.sleep(0.5)
    
    # Get results
    results_response = requests.get(f"{BASE_URL}/api/scraping/results/{task_id}")
    results = results_response.json()
    
    successful = sum(1 for r in results if r['success'])
    print(f"✅ Processed {len(results)} URLs")
    print(f"   Successful: {successful}")
    print(f"   Failed: {len(results) - successful}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['url']}")
        if result['success']:
            data = result['data']
            print(f"      Title: {data.get('page_title', data.get('title', 'N/A'))[:50]}...")
            print(f"      Content: {len(data.get('content', ''))} characters")
            print(f"      Links: {data.get('metadata', {}).get('link_count', 0)}")
    
    print()

def example_4_search_functionality():
    """Example 4: Search functionality"""
    print("🔎 Example 4: Search Functionality")
    print("-" * 40)
    
    queries = ["python programming", "web development", "machine learning"]
    
    for query in queries:
        response = requests.post(
            f"{BASE_URL}/api/scraping/search",
            params={"query": query, "max_results": 3}
        )
        
        search_data = response.json()
        print(f"✅ Query: '{query}'")
        print(f"   Results: {search_data['count']} items")
        
        for i, result in enumerate(search_data['results'], 1):
            print(f"   {i}. {result['description']}")
            print(f"      URL: {result['url']}")
        print()

def example_5_url_validation():
    """Example 5: URL validation"""
    print("✅ Example 5: URL Validation")
    print("-" * 40)
    
    test_urls = [
        "https://python.org",
        "https://example.com",
        "https://this-url-does-not-exist-12345.com"
    ]
    
    for url in test_urls:
        response = requests.post(
            f"{BASE_URL}/api/scraping/validate-url",
            params={"url": url}
        )
        
        validation_data = response.json()
        status = "✅" if validation_data['valid'] else "❌"
        print(f"{status} {url}")
        print(f"   Valid: {validation_data['valid']}")
        print(f"   Status Code: {validation_data.get('status_code', 'N/A')}")
        print(f"   Content Type: {validation_data.get('content_type', 'N/A')}")
        
        if 'error' in validation_data:
            print(f"   Error: {validation_data['error']}")
        print()

def example_6_error_handling():
    """Example 6: Error handling"""
    print("⚠️ Example 6: Error Handling")
    print("-" * 40)
    
    # Test with invalid URLs
    payload = {
        "urls": [
            "https://this-domain-does-not-exist-12345.com",
            "not-a-valid-url",
            "https://example.com/invalid-page-404"
        ],
        "prompt": "Extract content"
    }
    
    response = requests.post(f"{BASE_URL}/api/scraping/execute", json=payload)
    task_id = response.json()['task_id']
    
    # Wait for completion
    while True:
        status_response = requests.get(f"{BASE_URL}/api/scraping/status/{task_id}")
        status = status_response.json()['status']
        
        if status in ['completed', 'failed']:
            break
        time.sleep(0.5)
    
    # Get results
    results_response = requests.get(f"{BASE_URL}/api/scraping/results/{task_id}")
    results = results_response.json()
    
    print("Error handling results:")
    for result in results:
        if result['success']:
            print(f"✅ {result['url']} - Success")
        else:
            print(f"❌ {result['url']} - {result['error']}")
    
    print()

def main():
    """Run all examples"""
    print("🚀 ScrapeGraph Enhanced - Usage Examples")
    print("=" * 50)
    print("Make sure the API server is running:")
    print("  cd backend && source venv/bin/activate")
    print("  uvicorn app.main:app --reload")
    print()
    
    try:
        # Test server connection
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ Server not running. Please start the server first.")
            return
        
        print("✅ Server is running. Starting examples...\n")
        
        # Run examples
        example_1_basic_scraping()
        example_2_structured_extraction()
        example_3_batch_processing()
        example_4_search_functionality()
        example_5_url_validation()
        example_6_error_handling()
        
        print("🎉 All examples completed!")
        print("\nFor more information, see:")
        print("- SCRAPEGRAPH_USER_GUIDE.md")
        print("- http://localhost:8000/docs (API documentation)")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    main()