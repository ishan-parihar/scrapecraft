"""
Comprehensive Test Suite for Technical Intelligence Service
Phase 3 Week 10: Technical Intelligence
"""

import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, patch, AsyncMock

# Import the service we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.technical_intelligence_service import (
    TechnicalIntelligenceService,
    WHOISRecord,
    DNSRecord,
    NetworkNode,
    DarkWebContent,
    SSLCertificate,
    gather_technical_intelligence
)


class TestTechnicalIntelligenceService:
    """Test suite for TechnicalIntelligenceService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return TechnicalIntelligenceService()
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session"""
        session = Mock()
        session.get = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def sample_whois_record(self):
        """Sample WHOIS record for testing"""
        return WHOISRecord(
            domain="example.com",
            registrar="Example Registrar",
            creation_date=date(2020, 1, 15),
            expiration_date=date(2025, 1, 15),
            status=["clientTransferProhibited"],
            name_servers=["ns1.example.com", "ns2.example.com"],
            registrant_name="John Doe",
            registrant_org="Example Corp",
            registrant_country="US",
            confidence=0.9,
            source="RDAP"
        )

    @pytest.fixture
    def sample_dns_record(self):
        """Sample DNS record for testing"""
        return DNSRecord(
            domain="example.com",
            record_type="A",
            value="192.0.2.1",
            ttl=3600,
            timestamp=datetime.now(),
            confidence=0.95,
            source="DNS Resolver"
        )

    @pytest.fixture
    def sample_network_node(self):
        """Sample network node for testing"""
        return NetworkNode(
            ip_address="192.0.2.1",
            hostname="example.com",
            asn="AS12345",
            asn_org="Example ISP",
            country="US",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            isp="Example ISP",
            organization="Example Corp",
            node_type="server",
            open_ports=[80, 443],
            services=["HTTP", "HTTPS"],
            confidence=0.85,
            source="ipinfo.io"
        )

    @pytest.fixture
    def sample_ssl_certificate(self):
        """Sample SSL certificate for testing"""
        return SSLCertificate(
            domain="example.com",
            certificate_issuer="Let's Encrypt",
            certificate_subject="example.com",
            serial_number="1234567890ABCDEF",
            signature_algorithm="sha256WithRSAEncryption",
            key_size=2048,
            valid_from=date(2024, 1, 1),
            valid_until=date(2025, 1, 1),
            alternative_names=["www.example.com", "mail.example.com"],
            certificate_transparency=True,
            confidence=0.8,
            source="crt.sh"
        )

    @pytest.fixture
    def sample_dark_web_content(self):
        """Sample dark web content for testing"""
        return DarkWebContent(
            title="Discussion about example.com breach",
            url="http://demo7fy2pt7ngd5q3.onion/forum/thread/12345",
            content_type="forum",
            description="Users discussing recent security breach",
            author="Anonymous",
            post_date=date.today(),
            keywords=["example.com", "breach", "security"],
            mentions=["example.com"],
            threat_level="high",
            credibility=0.6,
            confidence=0.7,
            source="Ahmia.fi"
        )

    @pytest.mark.asyncio
    async def test_whois_lookup(self, service):
        """Test WHOIS lookup functionality"""
        
        # Mock RDAP response
        mock_rdap_data = {
            "entities": [
                {
                    "vcardArray": [
                        "vcard",
                        [
                            ["fn", {}, "text", "John Doe"],
                            ["org", {}, "text", "Example Corp"],
                            ["email", {}, "text", "admin@example.com"]
                        ]
                    ],
                    "roles": ["registrant"]
                }
            ],
            "events": [
                {"eventAction": "registration", "eventDate": "2020-01-15T00:00:00Z"},
                {"eventAction": "expiration", "eventDate": "2025-01-15T00:00:00Z"},
                {"eventAction": "last changed", "eventDate": "2023-06-01T00:00:00Z"}
            ],
            "status": ["clientTransferProhibited"],
            "secureDNS": {"delegationKeys": [{}]},
            "remarks": [
                {
                    "title": "Nameservers",
                    "description": ["ns1.example.com", "ns2.example.com"]
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_rdap_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                result = await service.perform_whois_lookup("example.com")
                
                assert isinstance(result, WHOISRecord)
                assert result.domain == "example.com"
                assert result.registrant_name == "John Doe"
                assert result.registrant_org == "Example Corp"
                assert result.registrant_email == "admin@example.com"
                assert result.creation_date == date(2020, 1, 15)
                assert result.expiration_date == date(2025, 1, 15)
                assert "clientTransferProhibited" in result.status
                assert result.dnssec == True

    @pytest.mark.asyncio
    async def test_dns_analysis(self, service):
        """Test DNS record analysis"""
        
        # Mock DNS resolver response
        with patch('dns.resolver.Resolver.resolve') as mock_resolve:
            mock_answer = Mock()
            mock_answer.ttl = 3600
            mock_answer.__str__ = lambda: "192.0.2.1"
            
            mock_resolve.return_value = [mock_answer]
            
            async with service:
                results = await service.analyze_dns_records("example.com", ["A"])
                
                assert len(results) > 0
                assert isinstance(results[0], DNSRecord)
                assert results[0].domain == "example.com"
                assert results[0].record_type == "A"
                assert results[0].value == "192.0.2.1"
                assert results[0].ttl == 3600
                assert results[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_network_mapping(self, service):
        """Test network infrastructure mapping"""
        
        # Mock DNS resolver for IP resolution
        with patch('dns.resolver.Resolver.resolve') as mock_resolve, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock DNS A record
            mock_answer = Mock()
            mock_answer.__str__ = lambda: "192.0.2.1"
            mock_resolve.return_value = [mock_answer]
            
            # Mock IP info response
            mock_ip_data = {
                "hostname": "example.com",
                "org": "AS12345 Example ISP",
                "country": "US",
                "region": "California",
                "city": "San Francisco",
                "loc": "37.7749,-122.4194"
            }
            
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_ip_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.map_network_infrastructure("example.com")
                
                assert len(results) > 0
                assert isinstance(results[0], NetworkNode)
                assert results[0].ip_address == "192.0.2.1"
                assert results[0].hostname == "example.com"
                assert results[0].country == "US"
                assert results[0].asn == "AS12345"
                assert results[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_ssl_certificate_analysis(self, service):
        """Test SSL certificate analysis"""
        
        # Mock certificate transparency log response
        mock_cert_data = [
            {
                "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
                "name_value": "example.com\nwww.example.com",
                "serial_number": "1234567890ABCDEF",
                "not_before": "2024-01-01T00:00:00",
                "not_after": "2025-01-01T00:00:00"
            }
        ]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=json.dumps(mock_cert_data))
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                results = await service.analyze_ssl_certificates("example.com")
                
                assert len(results) > 0
                assert isinstance(results[0], SSLCertificate)
                assert results[0].domain == "example.com"
                assert "Let's Encrypt" in results[0].certificate_issuer
                assert results[0].serial_number == "1234567890ABCDEF"
                assert results[0].valid_from == date(2024, 1, 1)
                assert results[0].valid_until == date(2025, 1, 1)
                assert "www.example.com" in results[0].alternative_names

    @pytest.mark.asyncio
    async def test_dark_web_monitoring(self, service):
        """Test dark web monitoring"""
        
        # Mock dark web search response
        mock_html = """
        <html>
            <body>
                <div class="searchResult">
                    <a href="http://demo7fy2pt7ngd5q3.onion/thread/123">Discussion about example.com</a>
                    <p class="description">Users discussing security breach</p>
                </div>
                <div class="searchResult">
                    <a href="http://demo7fy2pt7ngd5q3.onion/thread/456">Market selling example.com data</a>
                    <p class="description">Data marketplace listing</p>
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
                results = await service.monitor_dark_web(["example.com"])
                
                assert len(results) > 0
                assert isinstance(results[0], DarkWebContent)
                assert "example.com" in results[0].title
                assert results[0].content_type in ["forum", "market", "blog", "leak"]
                assert results[0].threat_level in ["low", "medium", "high", "critical"]
                assert "example.com" in results[0].mentions

    @pytest.mark.asyncio
    async def test_ip_address_analysis(self, service):
        """Test individual IP address analysis"""
        
        mock_ip_data = {
            "hostname": "example.com",
            "org": "AS12345 Example ISP",
            "country": "US",
            "region": "California",
            "city": "San Francisco",
            "loc": "37.7749,-122.4194"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_ip_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with service:
                result = await service._analyze_ip_address("192.0.2.1")
                
                assert isinstance(result, NetworkNode)
                assert result.ip_address == "192.0.2.1"
                assert result.hostname == "example.com"
                assert result.asn == "AS12345"
                assert result.country == "US"
                assert result.latitude == 37.7749
                assert result.longitude == -122.4194

    @pytest.mark.asyncio
    async def test_fallback_whois(self, service):
        """Test fallback WHOIS functionality"""
        
        with patch('dns.resolver.Resolver.resolve') as mock_resolve:
            mock_ns = Mock()
            mock_ns.__str__ = lambda: "ns1.example.com"
            mock_resolve.return_value = [mock_ns]
            
            result = await service._fallback_whois("example.com")
            
            assert isinstance(result, WHOISRecord)
            assert result.domain == "example.com"
            assert result.source == "Fallback WHOIS"
            assert "ns1.example.com" in result.name_servers
            assert "active" in result.status

    @pytest.mark.asyncio
    async def test_additional_node_discovery(self, service):
        """Test additional network node discovery"""
        
        with patch('dns.resolver.Resolver.resolve') as mock_resolve, \
             patch.object(service, '_analyze_ip_address') as mock_analyze:
            
            # Mock subdomain resolution
            mock_ip = Mock()
            mock_ip.__str__ = lambda: "192.0.2.2"
            mock_resolve.return_value = [mock_ip]
            
            # Mock IP analysis
            mock_node = NetworkNode(ip_address="192.0.2.2", hostname="www.example.com")
            mock_analyze.return_value = mock_node
            
            results = await service._discover_additional_nodes("example.com")
            
            assert len(results) > 0
            assert results[0].hostname == "www.example.com"

    @pytest.mark.asyncio
    async def test_demo_dark_web_content_generation(self, service):
        """Test demo dark web content generation"""
        
        search_terms = ["example.com", "test"]
        
        results = await service._generate_demo_dark_web_content(search_terms)
        
        assert len(results) > 0
        assert isinstance(results[0], DarkWebContent)
        assert results[0].confidence == 0.3  # Demo confidence level
        assert results[0].source == "Demo Data"
        assert any(term in results[0].title for term in search_terms)

    def test_ip_address_validation(self, service):
        """Test IP address validation"""
        
        assert service._is_ip_address("192.0.2.1") == True
        assert service._is_ip_address("2001:db8::1") == True
        assert service._is_ip_address("example.com") == False
        assert service._is_ip_address("invalid") == False

    def test_certificate_date_parsing(self, service):
        """Test SSL certificate date parsing"""
        
        # Test ISO format
        iso_date = "2024-01-01T00:00:00Z"
        parsed = service._parse_cert_date(iso_date)
        assert parsed == date(2024, 1, 1)
        
        # Test simple date format
        simple_date = "2024-01-01"
        parsed = service._parse_cert_date(simple_date)
        assert parsed == date(2024, 1, 1)
        
        # Test invalid date
        invalid_date = "invalid"
        parsed = service._parse_cert_date(invalid_date)
        assert parsed is None

    def test_content_type_classification(self, service):
        """Test dark web content type classification"""
        
        assert service._classify_content_type("Market selling data") == "market"
        assert service._classify_content_type("Forum discussion") == "forum"
        assert service._classify_content_type("Latest data leak") == "leak"
        assert service._classify_content_type("Blog post") == "blog"

    def test_threat_level_assessment(self, service):
        """Test threat level assessment"""
        
        keywords = ["example.com"]
        
        high_threat_title = "Major breach of example.com database"
        medium_threat_title = "Discussion about example.com security"
        low_threat_title = "Information about example.com"
        
        assert service._assess_threat_level(high_threat_title, keywords) == "high"
        assert service._assess_threat_level(medium_threat_title, keywords) == "medium"
        assert service._assess_threat_level(low_threat_title, keywords) == "low"

    def test_node_deduplication(self, service, sample_network_node):
        """Test network node deduplication"""
        
        node2 = NetworkNode(
            ip_address="192.0.2.2",
            hostname="example.org",
            confidence=0.8
        )
        
        duplicate_node = NetworkNode(
            ip_address="192.0.2.1",  # Same IP as sample
            hostname="duplicate.com",
            confidence=0.7
        )
        
        nodes = [sample_network_node, node2, duplicate_node]
        unique_nodes = service._deduplicate_nodes(nodes)
        
        assert len(unique_nodes) == 2  # Duplicate removed
        assert unique_nodes[0].ip_address == "192.0.2.1"
        assert unique_nodes[1].ip_address == "192.0.2.2"

    def test_certificate_deduplication(self, service, sample_ssl_certificate):
        """Test SSL certificate deduplication"""
        
        cert2 = SSLCertificate(
            domain="test.com",
            serial_number="FEDCBA0987654321",  # Different serial
            confidence=0.8
        )
        
        duplicate_cert = SSLCertificate(
            domain="example.org",
            serial_number="1234567890ABCDEF",  # Same serial as sample
            confidence=0.7
        )
        
        certificates = [sample_ssl_certificate, cert2, duplicate_cert]
        unique_certs = service._deduplicate_certificates(certificates)
        
        assert len(unique_certs) == 2  # Duplicate removed
        assert unique_certs[0].serial_number == "1234567890ABCDEF"
        assert unique_certs[1].serial_number == "FEDCBA0987654321"

    @pytest.mark.asyncio
    async def test_comprehensive_technical_footprint(self, service):
        """Test comprehensive technical footprint analysis"""
        
        with patch.object(service, 'perform_whois_lookup') as mock_whois, \
             patch.object(service, 'analyze_dns_records') as mock_dns, \
             patch.object(service, 'map_network_infrastructure') as mock_network, \
             patch.object(service, 'analyze_ssl_certificates') as mock_ssl, \
             patch.object(service, 'monitor_dark_web') as mock_dark:
            
            # Mock return values
            mock_whois.return_value = WHOISRecord(domain="example.com", confidence=0.9)
            mock_dns.return_value = [DNSRecord(domain="example.com", record_type="A", value="192.0.2.1")]
            mock_network.return_value = [NetworkNode(ip_address="192.0.2.1", confidence=0.8)]
            mock_ssl.return_value = [SSLCertificate(domain="example.com", confidence=0.8)]
            mock_dark.return_value = []
            
            async with service:
                analysis = await service.analyze_technical_footprint("example.com")
                
                assert 'target' in analysis
                assert analysis['target'] == "example.com"
                assert 'whois' in analysis
                assert 'dns_records' in analysis
                assert 'network_nodes' in analysis
                assert 'ssl_certificates' in analysis
                assert 'dark_web_mentions' in analysis
                assert 'risk_assessment' in analysis
                assert 'infrastructure_summary' in analysis
                
                # Check risk assessment structure
                risk = analysis['risk_assessment']
                assert 'overall_risk' in risk
                assert 'risk_factors' in risk
                assert 'security_recommendations' in risk
                
                # Check infrastructure summary
                summary = analysis['infrastructure_summary']
                assert 'total_ips' in summary
                assert 'countries' in summary
                assert 'asns' in summary
                assert 'open_ports' in summary
                assert 'certificate_issues' in summary

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling in technical intelligence operations"""
        
        # Test network error in WHOIS lookup
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            async with service:
                # Should not raise exception, should return fallback result
                result = await service.perform_whois_lookup("example.com")
                assert isinstance(result, WHOISRecord)
                assert result.confidence <= 0.5  # Lower confidence for fallback

    @pytest.mark.asyncio
    async def test_rate_limiting(self, service):
        """Test rate limiting between requests"""
        
        call_count = 0
        
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={})
            mock_response.text = AsyncMock(return_value="[]")
            return mock_response.__aenter__.return_value
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            async with service:
                # Perform multiple operations
                await service.monitor_dark_web(["test1"])
                await service.monitor_dark_web(["test2"])
                
                # Should have made multiple calls
                assert call_count >= 2

    def test_data_classes(self):
        """Test data class structure"""
        
        # Test WHOISRecord
        whois = WHOISRecord(
            domain="example.com",
            registrar="Test Registrar",
            confidence=0.9
        )
        
        assert whois.domain == "example.com"
        assert whois.registrar == "Test Registrar"
        assert whois.confidence == 0.9
        assert isinstance(whois.status, list)
        assert isinstance(whois.name_servers, list)
        
        # Test DNSRecord
        dns = DNSRecord(
            domain="example.com",
            record_type="A",
            value="192.0.2.1",
            confidence=0.95
        )
        
        assert dns.domain == "example.com"
        assert dns.record_type == "A"
        assert dns.value == "192.0.2.1"
        
        # Test NetworkNode
        node = NetworkNode(
            ip_address="192.0.2.1",
            hostname="example.com",
            confidence=0.8
        )
        
        assert node.ip_address == "192.0.2.1"
        assert node.hostname == "example.com"
        assert isinstance(node.open_ports, list)
        assert isinstance(node.services, list)
        
        # Test DarkWebContent
        content = DarkWebContent(
            title="Test Content",
            url="http://example.onion/",
            content_type="forum",
            confidence=0.7
        )
        
        assert content.title == "Test Content"
        assert content.content_type == "forum"
        assert isinstance(content.keywords, list)
        assert isinstance(content.mentions, list)
        
        # Test SSLCertificate
        cert = SSLCertificate(
            domain="example.com",
            certificate_issuer="Test CA",
            confidence=0.8
        )
        
        assert cert.domain == "example.com"
        assert cert.certificate_issuer == "Test CA"
        assert isinstance(cert.alternative_names, list)

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
    async def test_convenience_function(self):
        """Test the convenience function for technical intelligence"""
        
        mock_analysis = {
            'target': 'example.com',
            'timestamp': datetime.now().isoformat(),
            'risk_assessment': {'overall_risk': 'low'}
        }
        
        with patch('app.services.technical_intelligence_service.TechnicalIntelligenceService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.analyze_technical_footprint.return_value = mock_analysis
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            result = await gather_technical_intelligence("example.com")
            
            assert result['target'] == "example.com"
            mock_service.analyze_technical_footprint.assert_called_once_with("example.com")


# Performance tests
class TestTechnicalIntelligencePerformance:
    """Performance tests for technical intelligence service"""
    
    @pytest.mark.asyncio
    async def test_analysis_performance(self):
        """Test analysis performance benchmarks"""
        
        service = TechnicalIntelligenceService()
        
        # Mock quick responses
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('dns.resolver.Resolver.resolve') as mock_resolve:
            
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={})
            mock_response.text = AsyncMock(return_value="[]")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            mock_answer = Mock()
            mock_answer.__str__ = lambda: "192.0.2.1"
            mock_answer.ttl = 3600
            mock_resolve.return_value = [mock_answer]
            
            start_time = asyncio.get_event_loop().time()
            
            async with service:
                await service.analyze_dns_records("example.com")
                await service.map_network_infrastructure("example.com")
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (e.g., 30 seconds)
            assert duration < 30.0

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """Test concurrent analysis capability"""
        
        service = TechnicalIntelligenceService()
        
        # Mock responses
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('dns.resolver.Resolver.resolve') as mock_resolve:
            
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={})
            mock_response.text = AsyncMock(return_value="[]")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            mock_answer = Mock()
            mock_answer.__str__ = lambda: "192.0.2.1"
            mock_answer.ttl = 3600
            mock_resolve.return_value = [mock_answer]
            
            async with service:
                # Run multiple analyses concurrently
                tasks = [
                    service.analyze_dns_records(f"example{i}.com")
                    for i in range(3)
                ]
                
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 3
                assert all(isinstance(r, list) for r in results)


# Integration tests
class TestTechnicalIntelligenceIntegration:
    """Integration tests for technical intelligence service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end technical intelligence workflow"""
        
        target = "example.com"
        
        # Test the complete workflow
        result = await gather_technical_intelligence(target)
        
        # Verify structure
        assert 'target' in result
        assert result['target'] == target
        assert 'whois' in result
        assert 'dns_records' in result
        assert 'network_nodes' in result
        assert 'ssl_certificates' in result
        assert 'dark_web_mentions' in result
        assert 'risk_assessment' in result
        assert 'infrastructure_summary' in result
        
        # Verify risk assessment structure
        risk = result['risk_assessment']
        assert isinstance(risk['overall_risk'], str)
        assert isinstance(risk['risk_factors'], list)
        assert isinstance(risk['security_recommendations'], list)
        
        # Verify infrastructure summary
        summary = result['infrastructure_summary']
        assert isinstance(summary['total_ips'], int)
        assert isinstance(summary['countries'], (set, list))
        assert isinstance(summary['asns'], (set, list))

    @pytest.mark.asyncio
    async def test_real_api_integration(self):
        """Test with real API endpoints (if available)"""
        
        # This test would only run with real API access
        # Skip for now as it requires actual API access
        pytest.skip("Requires real API access")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k", "test_whois_lookup"])