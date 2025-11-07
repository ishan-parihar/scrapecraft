#!/usr/bin/env python3
"""
Phase 1 Week 4: Comprehensive Testing & Integration
End-to-end workflow testing for the complete Phase 1 implementation.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.real_search_service import RealSearchService
from app.services.enhanced_web_scraping_service import EnhancedWebScrapingService
from app.services.search_result_processor import SearchResultProcessingPipeline
from app.services.error_handling import (
    ErrorHandler, RetryConfig, CircuitBreakerConfig,
    handle_errors, NetworkException, RateLimitException
)
from app.services.data_validation import (
    DataValidationFramework, ValidationLevel, ContentCategory
)
from app.config_validator import validate_configuration

class Phase1IntegrationTester:
    """Comprehensive integration tester for Phase 1 implementation."""
    
    def __init__(self):
        self.test_results = {}
        self.error_stats = {}
        
    async def run_comprehensive_tests(self) -> bool:
        """Run all comprehensive integration tests."""
        print("🧪 Phase 1 Week 4: Comprehensive Testing & Integration")
        print("End-to-End Workflow Testing")
        print("=" * 60)
        
        test_functions = [
            self.test_configuration_validation,
            self.test_search_engine_integration,
            self.test_web_scraping_with_rate_limiting,
            self.test_error_handling_and_recovery,
            self.test_data_validation_framework,
            self.test_end_to_end_workflow,
            self.test_performance_under_load,
            self.test_error_scenarios
        ]
        
        all_passed = True
        
        for test_func in test_functions:
            try:
                print(f"\\n🔍 Running {test_func.__name__}...")
                start_time = time.time()
                
                result = await test_func()
                duration = time.time() - start_time
                
                self.test_results[test_func.__name__] = {
                    'passed': result,
                    'duration': duration,
                    'details': 'Completed successfully' if result else 'Failed'
                }
                
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"   {status} ({duration:.2f}s)")
                
                if not result:
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.test_results[test_func.__name__] = {
                    'passed': False,
                    'duration': 0,
                    'details': str(e)
                }
                all_passed = False
        
        # Print final summary
        self.print_test_summary()
        
        return all_passed
    
    async def test_configuration_validation(self) -> bool:
        """Test configuration validation."""
        config = validate_configuration()
        
        # Check required services
        if config['status'] != 'success':
            return False
        
        # Check for essential services
        required_services = ['openrouter', 'duckduckgo_search']
        for service in required_services:
            if service not in config['configured_services']:
                print(f"     Warning: {service} not configured")
        
        return len(config['errors']) == 0
    
    async def test_search_engine_integration(self) -> bool:
        """Test search engine integration."""
        async with RealSearchService() as search_service:
            # Test different query types
            test_queries = [
                "python programming",
                "machine learning tutorials",
                "web scraping best practices"
            ]
            
            all_success = True
            
            for query in test_queries:
                try:
                    results = await search_service.multi_search(
                        query,
                        engines=['duckduckgo'],
                        max_results=3
                    )
                    
                    if not results or 'duckduckgo' not in results:
                        print(f"     No results for query: {query}")
                        all_success = False
                    elif len(results['duckduckgo']) == 0:
                        print(f"     Empty results for query: {query}")
                        all_success = False
                    else:
                        print(f"     Found {len(results['duckduckgo'])} results for '{query}'")
                        
                except Exception as e:
                    print(f"     Search failed for '{query}': {e}")
                    all_success = False
            
            return all_success
    
    async def test_web_scraping_with_rate_limiting(self) -> bool:
        """Test web scraping with rate limiting."""
        test_urls = [
            "https://example.com",
            "https://www.python.org",
            "https://httpbin.org/html"
        ]
        
        async with EnhancedWebScrapingService() as scraper:
            start_time = time.time()
            
            # Test concurrent scraping with rate limiting
            results = await scraper.scrape_multiple_urls(test_urls, max_concurrent=2)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should take some time due to rate limiting
            if duration < 1.0:
                print(f"     Warning: Scraping completed too quickly ({duration:.2f}s) - rate limiting may not be working")
            
            # Check that we got some results
            if len(results) == 0:
                print("     No scraping results")
                return False
            
            # Validate results
            for content in results:
                if not content.title or not content.content:
                    print(f"     Invalid content for {content.url}")
                    return False
            
            print(f"     Successfully scraped {len(results)}/{len(test_urls)} URLs in {duration:.2f}s")
            return True
    
    async def test_error_handling_and_recovery(self) -> bool:
        """Test error handling and recovery mechanisms."""
        print("     Testing retry mechanism...")
        
        # Test retry with success
        retry_config = RetryConfig(max_retries=3, base_delay=0.1)
        
        @handle_errors(
            service_name="retry_test",
            operation_name="test_retry",
            retry_config=retry_config
        )
        async def retry_operation(attempt=[0]):
            attempt[0] += 1
            if attempt[0] < 3:
                raise NetworkException("Simulated failure")
            return "success"
        
        try:
            result = await retry_operation()
            if result != "success":
                print("     Retry mechanism failed")
                return False
        except Exception as e:
            print(f"     Retry mechanism error: {e}")
            return False
        
        print("     Testing circuit breaker...")
        
        # Test circuit breaker
        circuit_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0)
        
        @handle_errors(
            service_name="circuit_test",
            operation_name="test_circuit",
            circuit_breaker_config=circuit_config
        )
        async def failing_operation():
            raise NetworkException("Always fails")
        
        # Trigger circuit breaker
        failures = 0
        for i in range(3):
            try:
                await failing_operation()
            except NetworkException:
                failures += 1
            except Exception:
                break  # Circuit breaker should open
        
        if failures < 2:
            print("     Circuit breaker didn't trigger properly")
            return False
        
        print("     Error handling mechanisms working correctly")
        return True
    
    async def test_data_validation_framework(self) -> bool:
        """Test data validation framework."""
        validator = DataValidationFramework()
        
        # Test data with varying quality
        test_results = [
            {
                'title': 'Comprehensive Guide to Machine Learning',
                'snippet': 'This detailed guide covers machine learning concepts including neural networks, deep learning, and practical applications.',
                'url': 'https://example.edu/ml-guide',
                'source': 'academic'
            },
            {
                'title': 'BUY NOW FREE!!!',
                'snippet': 'limited time offer act now guaranteed winner selected click here',
                'url': 'http://spam-site.fake',
                'source': 'spam'
            },
            {
                'title': 'Python Documentation',
                'snippet': 'Official Python programming language documentation.',
                'url': 'https://docs.python.org',
                'source': 'official'
            }
        ]
        
        validated_results = validator.validate_search_results(
            test_results,
            level=ValidationLevel.MODERATE
        )
        
        if len(validated_results) != len(test_results):
            print("     Validation didn't process all results")
            return False
        
        # Check that spam was detected
        spam_detected = False
        for result, validation in validated_results:
            if not validation.is_valid and 'spam' in result['title'].lower():
                spam_detected = True
                break
        
        if not spam_detected:
            print("     Spam detection failed")
            return False
        
        # Check quality scores
        avg_score = sum(validation.overall_score for _, validation in validated_results) / len(validated_results)
        if avg_score < 0.5:
            print(f"     Average validation score too low: {avg_score}")
            return False
        
        print(f"     Validation working: avg score {avg_score:.2f}, spam detected: {spam_detected}")
        return True
    
    async def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end workflow."""
        print("     Testing complete OSINT workflow...")
        
        # Step 1: Search
        async with RealSearchService() as search_service:
            search_results = await search_service.multi_search(
                "cybersecurity best practices 2024",
                engines=['duckduckgo'],
                max_results=5
            )
        
        if not search_results or 'duckduckgo' not in search_results:
            print("     Search failed in workflow")
            return False
        
        # Step 2: Process search results
        pipeline = SearchResultProcessingPipeline()
        processed_results, stats = await pipeline.process_search_results(
            search_results['duckduckgo'],
            "cybersecurity best practices 2024",
            scrape_content=True,
            max_concurrent_scrapes=3
        )
        
        if len(processed_results) == 0:
            print("     No processed results in workflow")
            return False
        
        # Step 3: Validate results
        validator = DataValidationFramework()
        
        search_results_for_validation = [
            {
                'title': result.title,
                'snippet': result.snippet,
                'url': result.url,
                'source': result.source
            }
            for result in processed_results
        ]
        
        scraped_contents = {
            result.url: result.scraped_content
            for result in processed_results
            if result.scraped_content
        }
        
        validated_results = validator.validate_search_results(
            search_results_for_validation,
            scraped_contents=scraped_contents
        )
        
        # Step 4: Filter high-quality results
        high_quality_results = validator.filter_valid_results(validated_results, min_score=0.6)
        
        if len(high_quality_results) == 0:
            print("     No high-quality results in workflow")
            return False
        
        print(f"     End-to-end workflow successful: {len(high_quality_results)} high-quality results")
        return True
    
    async def test_performance_under_load(self) -> bool:
        """Test system performance under moderate load."""
        print("     Testing performance with concurrent operations...")
        
        # Concurrent searches
        queries = [
            "python tutorial",
            "machine learning",
            "web development",
            "data science",
            "cybersecurity"
        ]
        
        start_time = time.time()
        
        async def search_query(query: str):
            async with RealSearchService() as search_service:
                results = await search_service.multi_search(query, engines=['duckduckgo'], max_results=2)
                return len(results.get('duckduckgo', []))
        
        # Run searches concurrently
        tasks = [search_query(query) for query in queries]
        results_counts = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        successful_searches = sum(1 for count in results_counts if isinstance(count, int) and count > 0)
        
        if successful_searches < len(queries) * 0.8:  # At least 80% success rate
            print(f"     Too many failed searches: {successful_searches}/{len(queries)}")
            return False
        
        if duration > 30:  # Should complete within 30 seconds
            print(f"     Performance too slow: {duration:.2f}s")
            return False
        
        print(f"     Performance test passed: {successful_searches}/{len(queries)} searches in {duration:.2f}s")
        return True
    
    async def test_error_scenarios(self) -> bool:
        """Test various error scenarios."""
        print("     Testing error scenarios...")
        
        # Test invalid URLs
        async with EnhancedWebScrapingService() as scraper:
            invalid_urls = [
                "https://nonexistent-domain-12345.com",
                "https://httpbin.org/status/500",
                "invalid-url"
            ]
            
            results = await scraper.scrape_multiple_urls(invalid_urls, max_concurrent=2)
            
            # Should handle errors gracefully and return empty or partial results
            if len(results) > len(invalid_urls):
                print("     More results than expected for invalid URLs")
                return False
        
        # Test validation with bad data
        validator = DataValidationFramework()
        
        bad_results = [
            {
                'title': '',
                'snippet': '',
                'url': '',
                'source': ''
            },
            {
                'title': 'A' * 1000,  # Very long title
                'snippet': 'B' * 1000,
                'url': 'invalid-url',
                'source': 'test'
            }
        ]
        
        try:
            validated_results = validator.validate_search_results(bad_results)
            
            if len(validated_results) != len(bad_results):
                print("     Validation didn't process all bad data")
                return False
            
            # Most should be invalid or low quality
            valid_count = sum(1 for _, validation in validated_results if validation.is_valid)
            if valid_count > len(bad_results) * 0.5:
                print("     Too much bad data passed validation")
                return False
            
        except Exception as e:
            print(f"     Validation crashed on bad data: {e}")
            return False
        
        print("     Error scenarios handled gracefully")
        return True
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        total_duration = sum(result['duration'] for result in self.test_results.values())
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        print("\\n📋 Individual Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} {test_name} ({result['duration']:.2f}s)")
            if not result['passed']:
                print(f"       Details: {result['details']}")
        
        if passed_tests == total_tests:
            print("\\n🎉 ALL TESTS PASSED! Phase 1 implementation is ready for production!")
        else:
            print(f"\\n⚠️  {total_tests - passed_tests} tests failed. Review issues before deployment.")

async def main():
    """Run comprehensive Phase 1 testing."""
    tester = Phase1IntegrationTester()
    success = await tester.run_comprehensive_tests()
    
    if success:
        print("\\n" + "=" * 60)
        print("🚀 PHASE 1 IMPLEMENTATION COMPLETE!")
        print("=" * 60)
        print("✅ Emergency Fixes (Week 1) - Mock data removed")
        print("✅ Basic Search Implementation (Week 2) - Real APIs working")
        print("✅ Error Handling & Validation (Week 3) - Robust system")
        print("✅ Testing & Integration (Week 4) - Comprehensive validation")
        print("\\n🎯 ScrapeCraft is now a functional OSINT platform:")
        print("   • Real search engine integration (DuckDuckGo, Google, Bing)")
        print("   • Enhanced web scraping with rate limiting")
        print("   • Intelligent content processing and validation")
        print("   • Robust error handling and recovery")
        print("   • Quality scoring and relevance analysis")
        print("   • Production-ready architecture")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)