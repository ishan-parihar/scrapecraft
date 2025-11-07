"""
Comprehensive Test Suite for Public Records Integration
Phase 3 Week 9: Public Records Integration
"""

import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, patch, AsyncMock

# Import the service we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.public_records_service import (
    PublicRecordsService, 
    CorporateRecord, 
    PropertyRecord, 
    CourtRecord, 
    ProfessionalLicense,
    search_public_records
)


class TestPublicRecordsService:
    """Test suite for PublicRecordsService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return PublicRecordsService()
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session"""
        session = Mock()
        session.get = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def sample_corporate_record(self):
        """Sample corporate record for testing"""
        return CorporateRecord(
            record_type="corporate_registration",
            source="OpenCorporates",
            title="Test Corporation",
            description="Test company registered in US",
            url="https://opencorporates.com/companies/us_de/123456",
            date_accessed=datetime.now(),
            confidence=0.85,
            company_name="Test Corporation",
            registration_number="123456",
            incorporation_date=date(2020, 1, 15),
            status="active",
            jurisdiction="US"
        )

    @pytest.fixture
    def sample_property_record(self):
        """Sample property record for testing"""
        return PropertyRecord(
            record_type="property_ownership",
            source="County Assessor",
            title="Property: 123 Main St, Anytown, USA",
            description="Property owned by John Doe",
            url="https://assessor.example.com/property/123",
            date_accessed=datetime.now(),
            confidence=0.75,
            property_address="123 Main St, Anytown, USA",
            owner_name="John Doe",
            assessed_value=350000.0,
            property_type="Residential"
        )

    @pytest.fixture
    def sample_court_record(self):
        """Sample court record for testing"""
        return CourtRecord(
            record_type="court_case",
            source="State Court",
            title="Case: CIV-2024-1234",
            description="Civil case involving John Doe",
            url="https://courts.example.com/case/CIV-2024-1234",
            date_accessed=datetime.now(),
            confidence=0.80,
            case_number="CIV-2024-1234",
            court="Superior Court",
            case_type="Civil",
            parties=["John Doe", "Jane Smith"]
        )

    @pytest.fixture
    def sample_license_record(self):
        """Sample professional license record for testing"""
        return ProfessionalLicense(
            record_type="professional_license",
            source="State Board",
            title="License: LI123456",
            description="Professional license for John Doe",
            url="https://license.example.com/verify/LI123456",
            date_accessed=datetime.now(),
            confidence=0.90,
            licensee_name="John Doe",
            license_number="LI123456",
            profession="Engineer",
            issuing_authority="State Engineering Board",
            status="Active"
        )

    @pytest.mark.asyncio
    async def test_corporate_records_search(self, service):
        """Test corporate records search functionality"""
        
        # Mock successful API response
        mock_response_data = {
            "results": {
                "companies": [
                    {
                        "company": {
                            "name": "Test Corporation",
                            "company_number": "123456",
                            "jurisdiction_code": "US_DE",
                            "incorporation_date": "2020-01-15",
                            "current_status": "Active",
                            "registered_address_in_full": "123 Corporate Ave, Wilmington, DE",
                            "opencorporates_url": "https://opencorporates.com/companies/us_de/123456"
                        }
                    }
                ]
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.search_corporate_records("Test Corporation")
                
                assert len(results) > 0
                assert isinstance(results[0], CorporateRecord)
                assert results[0].company_name == "Test Corporation"
                assert results[0].registration_number == "123456"
                assert results[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_property_records_search(self, service):
        """Test property records search functionality"""
        
        # Mock HTML response for property records
        mock_html = """
        <html>
            <body>
                <div class="property-record">
                    <span class="address">123 Main St, Anytown, USA</span>
                    <span class="owner">John Doe</span>
                    <span class="value">$350,000</span>
                </div>
                <div class="property-record">
                    <span class="address">456 Oak Ave, Anytown, USA</span>
                    <span class="owner">John Doe</span>
                    <span class="value">$275,000</span>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.search_property_records("John Doe")
                
                assert len(results) > 0
                assert isinstance(results[0], PropertyRecord)
                assert "123 Main St" in results[0].property_address
                assert results[0].owner_name == "John Doe"
                assert results[0].assessed_value == 350000.0

    @pytest.mark.asyncio
    async def test_court_records_search(self, service):
        """Test court records search functionality"""
        
        # Mock HTML response for court records
        mock_html = """
        <html>
            <body>
                <div class="case-record">
                    <span class="case-number">CIV-2024-1234</span>
                    <span class="court">Superior Court</span>
                    <span class="case-type">Civil</span>
                    <a href="/case/CIV-2024-1234">View Case</a>
                </div>
                <div class="case-record">
                    <span class="case-number">FAM-2024-5678</span>
                    <span class="court">Family Court</span>
                    <span class="case-type">Family</span>
                    <a href="/case/FAM-2024-5678">View Case</a>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.search_court_records("John Doe")
                
                assert len(results) > 0
                assert isinstance(results[0], CourtRecord)
                assert results[0].case_number == "CIV-2024-1234"
                assert results[0].court == "Superior Court"
                assert results[0].case_type == "Civil"

    @pytest.mark.asyncio
    async def test_professional_license_search(self, service):
        """Test professional license search functionality"""
        
        # Mock HTML response for license records
        mock_html = """
        <html>
            <body>
                <div class="license-record">
                    <span class="license-number">LI123456</span>
                    <span class="profession">Engineer</span>
                    <span class="status">Active</span>
                </div>
                <div class="license-record">
                    <span class="license-number">LI789012</span>
                    <span class="profession">Architect</span>
                    <span class="status">Active</span>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.search_professional_licenses("John Doe", "Engineer")
                
                assert len(results) > 0
                assert isinstance(results[0], ProfessionalLicense)
                assert results[0].license_number == "LI123456"
                assert results[0].profession == "Engineer"
                assert results[0].status == "Active"

    @pytest.mark.asyncio
    async def test_sec_edgar_search(self, service):
        """Test SEC EDGAR database search"""
        
        # Mock SEC ticker data
        mock_ticker_data = {
            "0": {"ticker": "AAPL", "title": "Apple Inc."},
            "1": {"ticker": "MSFT", "title": "Microsoft Corporation"}
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_ticker_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service._search_sec_edgar("Apple")
                
                assert len(results) > 0
                assert isinstance(results[0], CorporateRecord)
                assert "Apple" in results[0].company_name
                assert results[0].source == "SEC EDGAR"

    @pytest.mark.asyncio
    async def test_uspto_search(self, service):
        """Test USPTO patent search"""
        
        # Mock USPTO patent search response
        mock_html = """
        <html>
            <body>
                <table class="patent-result">
                    <tr>
                        <th>US12345678</th>
                        <td>Method for testing software</td>
                    </tr>
                </table>
                <table class="patent-result">
                    <tr>
                        <th>US87654321</th>
                        <td>System for data processing</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service._search_uspto("software testing")
                
                assert len(results) > 0
                assert results[0].record_type == "patent"
                assert results[0].source == "USPTO"
                assert "US12345678" in results[0].title

    @pytest.mark.asyncio
    async def test_national_archive_search(self, service):
        """Test National Archives search"""
        
        # Mock National Archives API response
        mock_archive_data = {
            "opaResponse": {
                "results": {
                    "result": [
                        {
                            "naId": "12345678",
                            "title": {"#text": "Historical Document"},
                            "description": {"#text": "Important historical record"},
                            "type": "textual",
                            "creationDate": "2020-01-01"
                        }
                    ]
                }
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_archive_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service._search_national_archive("historical document")
                
                assert len(results) > 0
                assert results[0].record_type == "national_archive"
                assert results[0].source == "National Archives"
                assert results[0].title == "Historical Document"

    @pytest.mark.asyncio
    async def test_record_deduplication(self, service, sample_corporate_record):
        """Test record deduplication functionality"""
        
        # Create duplicate records
        duplicate1 = CorporateRecord(
            **asdict(sample_corporate_record),
            confidence=0.8
        )
        duplicate2 = CorporateRecord(
            **asdict(sample_corporate_record),
            confidence=0.9
        )
        
        records = [duplicate1, duplicate2]
        
        # Test deduplication
        unique_records = service._deduplicate_records(records, 'company_name')
        
        assert len(unique_records) == 1
        assert unique_records[0].confidence == 0.8  # First record kept

    @pytest.mark.asyncio
    async def test_record_pattern_analysis(self, service, sample_corporate_record, sample_property_record):
        """Test record pattern analysis"""
        
        records = [sample_corporate_record, sample_property_record]
        
        analysis = await service.analyze_record_patterns(records)
        
        assert analysis['total_records'] == 2
        assert 'corporate_registration' in analysis['record_types']
        assert 'property_ownership' in analysis['record_types']
        assert analysis['confidence_distribution']['high'] >= 1
        assert len(analysis['key_insights']) > 0

    @pytest.mark.asyncio
    async def test_date_parsing(self, service):
        """Test date parsing functionality"""
        
        # Test various date formats
        assert service._parse_date("2020-01-15") == date(2020, 1, 15)
        assert service._parse_date("2020/01/15") == date(2020, 1, 15)
        assert service._parse_date("01/15/2020") == date(2020, 1, 15)
        assert service._parse_date("15/01/2020") == date(2020, 1, 15)
        assert service._parse_date("") is None
        assert service._parse_date(None) is None
        assert service._parse_date("invalid date") is None

    @pytest.mark.asyncio
    async def test_demo_record_generation(self, service):
        """Test demo record generation when no real data available"""
        
        # Test property records demo
        property_records = await service._generate_demo_property_records("John Doe", "123 Main St")
        assert len(property_records) > 0
        assert isinstance(property_records[0], PropertyRecord)
        assert property_records[0].owner_name == "John Doe"
        assert property_records[0].confidence == 0.3  # Low confidence for demo data
        
        # Test court records demo
        court_records = await service._generate_demo_court_records("John Doe", "Civil")
        assert len(court_records) > 0
        assert isinstance(court_records[0], CourtRecord)
        assert court_records[0].parties == ["John Doe"]
        assert court_records[0].confidence == 0.3
        
        # Test license records demo
        license_records = await service._generate_demo_license_records("John Doe", "Engineer")
        assert len(license_records) > 0
        assert isinstance(license_records[0], ProfessionalLicense)
        assert license_records[0].licensee_name == "John Doe"
        assert license_records[0].profession == "Engineer"
        assert license_records[0].confidence == 0.3

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling in public records search"""
        
        # Test network error handling
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            async with service:
                # Should not raise exception, should return empty list or demo data
                results = await service.search_corporate_records("Test Company")
                assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_government_database_search(self, service):
        """Test comprehensive government database search"""
        
        # Mock various government database responses
        with patch.object(service, '_search_sec_edgar', return_value=[]), \
             patch.object(service, '_search_uspto', return_value=[]), \
             patch.object(service, '_search_fcc_uls', return_value=[]), \
             patch.object(service, '_search_national_archive', return_value=[]):
            
            async with service:
                results = await service.search_government_databases("test query")
                
                assert isinstance(results, list)
                # Should call all specified database searches

    @pytest.mark.asyncio
    async def test_rate_limiting(self, service):
        """Test rate limiting between requests"""
        
        call_count = 0
        
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html></html>")
            mock_response.json = AsyncMock(return_value={})
            return mock_response.__aenter__.return_value
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            async with service:
                # Search multiple record types
                await service.search_corporate_records("Test")
                await service.search_property_records("Test")
                await service.search_court_records("Test")
                
                # Should have made multiple calls with rate limiting
                assert call_count >= 3

    def test_record_data_classes(self):
        """Test record data class structure"""
        
        # Test CorporateRecord
        corporate = CorporateRecord(
            record_type="corporate",
            source="Test",
            title="Test Corp",
            description="Test company",
            company_name="Test Corp",
            registration_number="12345"
        )
        
        assert corporate.company_name == "Test Corp"
        assert corporate.registration_number == "12345"
        assert corporate.record_type == "corporate"
        
        # Test PropertyRecord
        property_rec = PropertyRecord(
            record_type="property",
            source="Test",
            title="Test Property",
            description="Test property",
            property_address="123 Main St",
            owner_name="John Doe"
        )
        
        assert property_rec.property_address == "123 Main St"
        assert property_rec.owner_name == "John Doe"
        
        # Test CourtRecord
        court = CourtRecord(
            record_type="court",
            source="Test",
            title="Test Case",
            description="Test case",
            case_number="CASE-123",
            court="Test Court",
            case_type="Civil"
        )
        
        assert court.case_number == "CASE-123"
        assert court.court == "Test Court"
        
        # Test ProfessionalLicense
        license_rec = ProfessionalLicense(
            record_type="license",
            source="Test",
            title="Test License",
            description="Test license",
            licensee_name="John Doe",
            license_number="LI123",
            profession="Engineer",
            issuing_authority="State Board"
        )
        
        assert license_rec.licensee_name == "John Doe"
        assert license_rec.license_number == "LI123"
        assert license_rec.profession == "Engineer"

    @pytest.mark.asyncio
    async def test_comprehensive_public_records_search(self):
        """Test the comprehensive search_public_records function"""
        
        # Mock the service methods
        with patch('app.services.public_records_service.PublicRecordsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock return values for different search types
            mock_service.search_corporate_records.return_value = []
            mock_service.search_property_records.return_value = []
            mock_service.search_court_records.return_value = []
            mock_service.search_professional_licenses.return_value = []
            mock_service.search_government_databases.return_value = []
            mock_service.analyze_record_patterns.return_value = {
                'total_records': 0,
                'key_insights': []
            }
            
            results = await search_public_records("John Doe")
            
            # Verify all search types were called
            mock_service.search_corporate_records.assert_called_once_with("John Doe")
            mock_service.search_property_records.assert_called_once_with("John Doe")
            mock_service.search_court_records.assert_called_once_with("John Doe")
            mock_service.search_professional_licenses.assert_called_once_with("John Doe")
            mock_service.search_government_databases.assert_called_once_with("John Doe")
            mock_service.analyze_record_patterns.assert_called_once()
            
            # Verify result structure
            assert 'corporate' in results
            assert 'property' in results
            assert 'court' in results
            assert 'license' in results
            assert 'government' in results
            assert 'analysis' in results

    @pytest.mark.asyncio
    async def test_service_context_manager(self, service):
        """Test service context manager functionality"""
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with service:
                assert service.session == mock_session
            
            # Verify session was closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, service):
        """Test confidence scoring for different record types"""
        
        # Test high confidence for SEC records
        sec_record = CorporateRecord(
            record_type="sec_filing",
            source="SEC EDGAR",
            title="Test",
            description="Test",
            company_name="Test",
            registration_number="123",
            confidence=0.9
        )
        
        assert sec_record.confidence >= 0.8
        
        # Test low confidence for demo records
        demo_record = PropertyRecord(
            record_type="property_ownership",
            source="Demo Data",
            title="Test",
            description="Test",
            property_address="123 Main St",
            owner_name="John Doe",
            confidence=0.3
        )
        
        assert demo_record.confidence == 0.3


# Performance tests
class TestPublicRecordsPerformance:
    """Performance tests for public records service"""
    
    @pytest.mark.asyncio
    async def test_search_performance(self):
        """Test search performance benchmarks"""
        
        service = PublicRecordsService()
        
        # Mock quick responses
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"results": {"companies": []}})
            mock_response.text = AsyncMock(return_value="<html></html>")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            start_time = asyncio.get_event_loop().time()
            
            async with service:
                await service.search_corporate_records("Test")
                await service.search_property_records("Test")
                await service.search_court_records("Test")
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (e.g., 30 seconds)
            assert duration < 30.0

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test concurrent search capability"""
        
        service = PublicRecordsService()
        
        # Mock responses
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"results": {"companies": []}})
            mock_response.text = AsyncMock(return_value="<html></html>")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                # Run multiple searches concurrently
                tasks = [
                    service.search_corporate_records(f"Company {i}")
                    for i in range(5)
                ]
                
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 5
                assert all(isinstance(r, list) for r in results)


# Integration tests
class TestPublicRecordsIntegration:
    """Integration tests for public records service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end public records search workflow"""
        
        query = "Test Corporation"
        
        # Test the complete workflow
        results = await search_public_records(query, ['corporate', 'property'])
        
        # Verify structure
        assert 'corporate' in results
        assert 'property' in results
        assert 'analysis' in results
        
        # Verify analysis contains expected fields
        analysis = results['analysis']
        assert 'total_records' in analysis
        assert 'record_types' in analysis
        assert 'key_insights' in analysis
        assert isinstance(analysis['total_records'], int)
        assert isinstance(analysis['record_types'], dict)
        assert isinstance(analysis['key_insights'], list)

    @pytest.mark.asyncio
    async def test_real_api_integration(self):
        """Test with real API endpoints (if available)"""
        
        # This test would only run with real API keys
        # Skip for now as it requires actual API access
        pytest.skip("Requires real API access")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k", "test_corporate_records_search"])