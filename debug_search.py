#!/usr/bin/env python3
"""
Debug script to analyze DuckDuckGo HTML response.
"""

import asyncio
import aiohttp
import re
from urllib.parse import urlencode

async def debug_duckduckgo():
    """Debug DuckDuckGo HTML parsing."""
    query = "artificial intelligence trends"
    
    print(f"🔍 Debugging DuckDuckGo search for: '{query}'")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            params = {'q': query}
            url = f"https://duckduckgo.com/html/?{urlencode(params)}"
            
            print(f"🌐 Requesting URL: {url}")
            
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                print(f"📊 Response status: {response.status}")
                html = await response.text()
                print(f"📏 HTML length: {len(html)} characters")
                
                # Show first few lines of HTML
                lines = html.split('\n')
                print("\n📄 First 10 lines of HTML:")
                print("-" * 40)
                for i, line in enumerate(lines[:10]):
                    print(f"{i+1:2d}: {line[:100]}")
                
                # Look for common patterns
                print("\n🔍 Looking for patterns:")
                print("-" * 40)
                
                patterns_to_check = [
                    ('result__a', 'class="result__a"'),
                    ('web-result', 'class="web-result"'),
                    ('result', 'class="result"'),
                    ('<a href=', 'Links'),
                    ('snippet', 'Snippet classes')
                ]
                
                for pattern_name, pattern in patterns_to_check:
                    matches = len(re.findall(pattern, html, re.IGNORECASE))
                    print(f"  {pattern_name:12}: {matches} matches")
                
                # Try to extract some results with different patterns
                print("\n🎯 Testing extraction patterns:")
                print("-" * 40)
                
                # Pattern 1: Look for result__a links
                result_a_matches = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.IGNORECASE)
                print(f"Pattern 1 (result__a): {len(result_a_matches)} results")
                for i, (url, title) in enumerate(result_a_matches[:3]):
                    print(f"  {i+1}. {title[:50]} -> {url[:50]}")
                
                # Pattern 2: Look for any links with titles
                any_link_matches = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]{10,100})</a>', html, re.IGNORECASE)
                print(f"Pattern 2 (any links): {len(any_link_matches)} results")
                for i, (url, title) in enumerate(any_link_matches[:3]):
                    if not any(skip in url.lower() for skip in ['duckduckgo', 'html', 'search']):
                        print(f"  {i+1}. {title[:50]} -> {url[:50]}")
                
                # Save full HTML for inspection
                with open('duckduckgo_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"\n💾 Full HTML saved to 'duckduckgo_debug.html'")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_duckduckgo())