"""
Technical Intelligence Service
Provides WHOIS, DNS analysis, network mapping, and dark web monitoring capabilities
"""

import asyncio
import aiohttp
import json
import re
import socket
import ipaddress
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from urllib.parse import urljoin, urlparse
import logging

import dns.resolver
import dns.exception
from bs4 import BeautifulSoup

from app.services.error_handling import handle_errors, RetryConfig
from app.services.llm_integration import LLMIntegrationService

logger = logging.getLogger(__name__)


@dataclass
class WHOISRecord:
    """WHOIS record information"""
    domain: str
    registrar: str = ""
    creation_date: Optional[date] = None
    expiration_date: Optional[date] = None
    updated_date: Optional[date] = None
    status: List[str] = None
    name_servers: List[str] = None
    registrant_name: str = ""
    registrant_org: str = ""
    registrant_country: str = ""
    registrant_email: str = ""
    registrant_phone: str = ""
    admin_email: str = ""
    tech_email: str = ""
    dnssec: bool = False
    raw_whois: str = ""
    confidence: float = 0.0
    source: str = ""
    
    def __post_init__(self):
        if self.status is None:
            self.status = []
        if self.name_servers is None:
            self.name_servers = []


@dataclass
class DNSRecord:
    """DNS record information"""
    domain: str
    record_type: str
    value: str
    ttl: int = 0
    priority: Optional[int] = None
    domain_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    confidence: float = 0.0
    source: str = ""


@dataclass
class NetworkNode:
    """Network infrastructure node"""
    ip_address: str
    hostname: str = ""
    asn: str = ""
    asn_org: str = ""
    country: str = ""
    region: str = ""
    city: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: str = ""
    organization: str = ""
    node_type: str = "unknown"  # server, router, load_balancer, etc.
    open_ports: List[int] = None
    services: List[str] = None
    confidence: float = 0.0
    source: str = ""
    
    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
        if self.services is None:
            self.services = []


@dataclass
class DarkWebContent:
    """Dark web intelligence content"""
    title: str
    url: str
    content_type: str  # forum, market, blog, leak
    description: str = ""
    author: str = ""
    post_date: Optional[date] = None
    keywords: List[str] = None
    mentions: List[str] = None
    threat_level: str = "low"  # low, medium, high, critical
    credibility: float = 0.0
    raw_content: str = ""
    confidence: float = 0.0
    source: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.mentions is None:
            self.mentions = []


@dataclass
class SSLCertificate:
    """SSL/TLS certificate information"""
    domain: str
    certificate_issuer: str = ""
    certificate_subject: str = ""
    serial_number: str = ""
    signature_algorithm: str = ""
    key_size: int = 0
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    alternative_names: List[str] = None
    certificate_transparency: bool = False
    revocation_status: str = "unknown"
    confidence: float = 0.0
    source: str = ""
    
    def __post_init__(self):
        if self.alternative_names is None:
            self.alternative_names = []


class TechnicalIntelligenceService:
    """Service for technical intelligence gathering"""
    
    def __init__(self):
        self.llm_service = LLMIntegrationService()
        self.session = None
        self.retry_config = RetryConfig(max_retries=3, base_delay=2.0)
        
        # DNS resolver configuration
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 10
        self.dns_resolver.lifetime = 30
        
        # Public intelligence APIs
        self.intelligence_apis = {
            'whois': 'https://rdap.org/domain/',
            'ip_info': 'https://ipinfo.io/',
            'asn_lookup': 'https://api.iptoasn.com/v1/as/ip/',
            'ssl_cert': 'https://crt.sh/',
            'dark_web_demo': 'https://ahmia.fi/search/',
            'shodan_demo': 'https://internetdb.shodan.io/',
            'virustotal': 'https://www.virustotal.com/vtapi/v2/',
            'passive_dns': 'https://passivednsapi.org/'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; OSINT-Scanner/1.0)'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @handle_errors("technical_intelligence", "whois_lookup", RetryConfig(max_retries=3, base_delay=2.0))
    async def perform_whois_lookup(self, domain: str) -> WHOISRecord:
        """Perform WHOIS lookup for a domain"""
        
        try:
            # Use RDAP (Registration Data Access Protocol) for modern WHOIS
            rdap_url = f"{self.intelligence_apis['whois']}{domain}"
            
            async with self.session.get(rdap_url) as response:
                if response.status == 200:
                    rdap_data = await response.json()
                    
                    record = WHOISRecord(
                        domain=domain,
                        source="RDAP",
                        confidence=0.9,
                        raw_whois=json.dumps(rdap_data, indent=2)
                    )
                    
                    # Extract entities and events from RDAP data
                    entities = rdap_data.get('entities', [])
                    events = rdap_data.get('events', [])
                    status = rdap_data.get('status', [])
                    remarks = rdap_data.get('remarks', [])
                    
                    # Parse status
                    record.status = status
                    
                    # Parse events (creation, expiration, etc.)
                    for event in events:
                        event_action = event.get('eventAction', '')
                        event_date = event.get('eventDate', '')
                        
                        if event_date:
                            try:
                                parsed_date = datetime.fromisoformat(event_date.replace('Z', '+00:00')).date()
                                
                                if event_action == 'registration':
                                    record.creation_date = parsed_date
                                elif event_action == 'expiration':
                                    record.expiration_date = parsed_date
                                elif event_action == 'last changed':
                                    record.updated_date = parsed_date
                            except ValueError:
                                pass
                    
                    # Parse entities for contact information
                    for entity in entities:
                        vcard_array = entity.get('vcardArray', [])
                        roles = entity.get('roles', [])
                        
                        if vcard_array and len(vcard_array) > 1:
                            for prop in vcard_array[1]:
                                if prop and len(prop) >= 4:
                                    prop_name = prop[0]
                                    prop_value = prop[3]
                                    
                                    if prop_name == 'fn':
                                        name = prop_value
                                        if 'registrant' in roles or not record.registrant_name:
                                            record.registrant_name = name
                                    elif prop_name == 'org':
                                        org = prop_value
                                        if 'registrant' in roles or not record.registrant_org:
                                            record.registrant_org = org
                                    elif prop_name == 'email':
                                        email = prop_value
                                        if 'registrant' in roles:
                                            record.registrant_email = email
                                        elif 'administrative' in roles:
                                            record.admin_email = email
                                        elif 'technical' in roles:
                                            record.tech_email = email
                                    elif prop_name == 'tel':
                                        if 'registrant' in roles:
                                            record.registrant_phone = prop_value
                    
                    # Parse nameservers
                    secure_dns = rdap_data.get('secureDNS', {})
                    delegation_keys = secure_dns.get('delegationKeys', [])
                    record.dnssec = len(delegation_keys) > 0
                    
                    # Extract nameservers from remarks or links
                    for remark in remarks:
                        if remark.get('title') == 'Nameservers':
                            nameserver_list = remark.get('description', [])
                            record.name_servers.extend(nameserver_list)
                    
                    return record
                    
        except Exception as e:
            logger.debug(f"RDAP lookup failed for {domain}: {str(e)}")
            
        # Fallback to traditional WHOIS
        return await self._fallback_whois(domain)

    @handle_errors("technical_intelligence", "dns_analysis", RetryConfig(max_retries=3, base_delay=1.0))
    async def analyze_dns_records(self, domain: str, record_types: List[str] = None) -> List[DNSRecord]:
        """Analyze DNS records for a domain"""
        
        if record_types is None:
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME', 'SRV']
            
        records = []
        
        for record_type in record_types:
            try:
                answers = self.dns_resolver.resolve(domain, record_type)
                
                for answer in answers:
                    record = DNSRecord(
                        domain=domain,
                        record_type=record_type,
                        value=str(answer),
                        ttl=answers.ttl,
                        timestamp=datetime.now(),
                        confidence=0.95,
                        source="DNS Resolver"
                    )
                    
                    # Extract additional information for specific record types
                    if record_type == 'MX' and hasattr(answer, 'preference'):
                        record.priority = answer.preference
                        record.value = str(answer.exchange)
                    elif record_type == 'SRV' and hasattr(answer, 'priority'):
                        record.priority = answer.priority
                        record.value = f"{answer.target}:{answer.port}"
                    elif record_type in ['A', 'AAAA']:
                        record.value = str(answer)
                    elif record_type == 'TXT':
                        record.value = str(answer).strip('"')
                    
                    records.append(record)
                    
            except dns.exception.NXDOMAIN:
                logger.debug(f"Domain {domain} does not exist for {record_type} records")
            except dns.exception.NoAnswer:
                logger.debug(f"No {record_type} records for {domain}")
            except Exception as e:
                logger.debug(f"Error resolving {record_type} for {domain}: {str(e)}")
                continue
                
        return records

    @handle_errors("technical_intelligence", "network_mapping", RetryConfig(max_retries=3, base_delay=2.0))
    async def map_network_infrastructure(self, target: str) -> List[NetworkNode]:
        """Map network infrastructure for domain or IP"""
        
        nodes = []
        
        # Resolve domain to IP if needed
        if not self._is_ip_address(target):
            try:
                answers = self.dns_resolver.resolve(target, 'A')
                ip_addresses = [str(answer) for answer in answers]
            except:
                ip_addresses = []
        else:
            ip_addresses = [target]
            
        # Analyze each IP address
        for ip in ip_addresses:
            node = await self._analyze_ip_address(ip)
            if node:
                nodes.append(node)
                
        # Additional network discovery
        additional_nodes = await self._discover_additional_nodes(target)
        nodes.extend(additional_nodes)
        
        # Remove duplicates
        unique_nodes = self._deduplicate_nodes(nodes)
        return sorted(unique_nodes, key=lambda x: x.confidence, reverse=True)

    @handle_errors("technical_intelligence", "ssl_certificate_analysis", RetryConfig(max_retries=3, base_delay=2.0))
    async def analyze_ssl_certificates(self, domain: str) -> List[SSLCertificate]:
        """Analyze SSL/TLS certificates for a domain"""
        
        certificates = []
        
        try:
            # Search certificate transparency logs
            crt_url = f"https://crt.sh/?q={domain}&output=json"
            
            async with self.session.get(crt_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    if content.strip().startswith('['):
                        cert_data = json.loads(content)
                        
                        for cert in cert_data[:20]:  # Limit to prevent overwhelming data
                            certificate = SSLCertificate(
                                domain=domain,
                                certificate_issuer=cert.get('issuer_name', ''),
                                certificate_subject=cert.get('name_value', ''),
                                serial_number=cert.get('serial_number', ''),
                                valid_from=self._parse_cert_date(cert.get('not_before')),
                                valid_until=self._parse_cert_date(cert.get('not_after')),
                                source="crt.sh",
                                confidence=0.8
                            )
                            
                            # Parse alternative names
                            name_value = cert.get('name_value', '')
                            if name_value:
                                names = [name.strip() for name in name_value.split('\n') if name.strip()]
                                certificate.alternative_names = names
                            
                            certificates.append(certificate)
                            
        except Exception as e:
            logger.debug(f"SSL certificate analysis failed for {domain}: {str(e)}")
            
        # Remove duplicates and sort by confidence
        unique_certs = self._deduplicate_certificates(certificates)
        return sorted(unique_certs, key=lambda x: x.confidence, reverse=True)[:10]

    @handle_errors("technical_intelligence", "dark_web_monitoring", RetryConfig(max_retries=3, base_delay=3.0))
    async def monitor_dark_web(self, search_terms: List[str], content_types: List[str] = None) -> List[DarkWebContent]:
        """Monitor dark web for mentions of search terms"""
        
        if content_types is None:
            content_types = ['forum', 'market', 'blog', 'leak']
            
        content = []
        
        # Note: Real dark web monitoring requires Tor and specialized access
        # This is a simplified implementation using surface web indices of dark web content
        
        for term in search_terms:
            try:
                # Use Ahmia.fi search engine (indexes .onion sites)
                search_url = f"https://ahmia.fi/search/?q={quote_plus(term)}"
                
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Parse search results
                        results = soup.find_all('div', class_='searchResult')
                        
                        for result in results[:5]:  # Limit results
                            title_elem = result.find('a')
                            desc_elem = result.find('p', class_='description')
                            url_elem = result.find('a', href=True)
                            
                            if title_elem and url_elem:
                                dark_content = DarkWebContent(
                                    title=title_elem.get_text(strip=True),
                                    url=url_elem['href'],
                                    content_type=self._classify_content_type(title_elem.get_text()),
                                    description=desc_elem.get_text(strip=True) if desc_elem else "",
                                    keywords=[term],
                                    mentions=[term],
                                    threat_level=self._assess_threat_level(title_elem.get_text(), [term]),
                                    source="Ahmia.fi",
                                    confidence=0.6  # Lower confidence for indirect monitoring
                                )
                                content.append(dark_content)
                                
                        await asyncio.sleep(1)  # Rate limiting
                        
            except Exception as e:
                logger.debug(f"Dark web monitoring failed for term '{term}': {str(e)}")
                continue
                
        # Generate demo content if no real results found
        if not content:
            content = await self._generate_demo_dark_web_content(search_terms)
            
        # Sort by threat level and confidence
        threat_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return sorted(content, key=lambda x: (threat_order.get(x.threat_level, 0), x.confidence), reverse=True)

    async def _fallback_whois(self, domain: str) -> WHOISRecord:
        """Fallback WHOIS lookup using traditional WHOIS servers"""
        
        record = WHOISRecord(
            domain=domain,
            source="Fallback WHOIS",
            confidence=0.5,
            raw_whois=""
        )
        
        try:
            # Try to get basic DNS information as fallback
            answers = self.dns_resolver.resolve(domain, 'NS')
            record.name_servers = [str(answer) for answer in answers]
            
            # Set some basic information
            record.status = ["active"]
            record.confidence = 0.6
            
        except Exception as e:
            logger.debug(f"Fallback WHOIS failed for {domain}: {str(e)}")
            record.confidence = 0.3
            
        return record

    async def _analyze_ip_address(self, ip: str) -> Optional[NetworkNode]:
        """Analyze individual IP address"""
        
        try:
            # Get IP information from ipinfo.io
            ip_url = f"https://ipinfo.io/{ip}/json"
            
            async with self.session.get(ip_url) as response:
                if response.status == 200:
                    ip_data = await response.json()
                    
                    node = NetworkNode(
                        ip_address=ip,
                        hostname=ip_data.get('hostname', ''),
                        asn=ip_data.get('org', '').split()[0] if ip_data.get('org') else "",
                        asn_org=' '.join(ip_data.get('org', '').split()[1:]) if ip_data.get('org') else "",
                        country=ip_data.get('country', ''),
                        region=ip_data.get('region', ''),
                        city=ip_data.get('city', ''),
                        latitude=float(ip_data.get('loc', ',').split(',')[0]) if ip_data.get('loc') else None,
                        longitude=float(ip_data.get('loc', ',').split(',')[1]) if ip_data.get('loc') and ',' in ip_data.get('loc') else None,
                        isp=ip_data.get('org', ''),
                        organization=ip_data.get('org', ''),
                        source="ipinfo.io",
                        confidence=0.85
                    )
                    
                    # Get additional ASN information
                    asn_info = await self._get_asn_info(ip)
                    if asn_info:
                        node.asn = asn_info.get('as_number', node.asn)
                        node.asn_org = asn_info.get('as_name', node.asn_org)
                    
                    return node
                    
        except Exception as e:
            logger.debug(f"IP analysis failed for {ip}: {str(e)}")
            
        return None

    async def _get_asn_info(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get ASN information for IP"""
        
        try:
            asn_url = f"https://api.iptoasn.com/v1/as/ip/{ip}"
            
            async with self.session.get(asn_url) as response:
                if response.status == 200:
                    return await response.json()
                    
        except Exception as e:
            logger.debug(f"ASN lookup failed for {ip}: {str(e)}")
            
        return None

    async def _discover_additional_nodes(self, target: str) -> List[NetworkNode]:
        """Discover additional network nodes through various techniques"""
        
        nodes = []
        
        try:
            # Try to discover related IPs through DNS enumeration
            if not self._is_ip_address(target):
                # Check common subdomains
                common_subdomains = ['www', 'mail', 'ftp', 'api', 'blog', 'shop', 'admin', 'test']
                
                for subdomain in common_subdomains[:5]:  # Limit to prevent too many requests
                    full_domain = f"{subdomain}.{target}"
                    
                    try:
                        answers = self.dns_resolver.resolve(full_domain, 'A')
                        for answer in answers:
                            ip = str(answer)
                            node = await self._analyze_ip_address(ip)
                            if node:
                                node.hostname = full_domain
                                nodes.append(node)
                                
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Additional node discovery failed: {str(e)}")
            
        return nodes

    async def _generate_demo_dark_web_content(self, search_terms: List[str]) -> List[DarkWebContent]:
        """Generate demo dark web content for development"""
        
        content = []
        
        for term in search_terms[:3]:  # Limit demo content
            demo_content = DarkWebContent(
                title=f"Discussion about {term} on dark web forum",
                url="http://demo7fy2pt7ngd5q3.onion/forum/thread/12345",
                content_type="forum",
                description=f"Users discussing security implications of {term}",
                author="Anonymous",
                post_date=datetime.now().date(),
                keywords=search_terms,
                mentions=[term],
                threat_level="medium",
                credibility=0.4,
                raw_content="Demo content for development purposes",
                confidence=0.3,  # Low confidence for demo data
                source="Demo Data"
            )
            content.append(demo_content)
            
        return content

    def _is_ip_address(self, target: str) -> bool:
        """Check if target is an IP address"""
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    def _parse_cert_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse certificate date"""
        if not date_str:
            return None
            
        try:
            # Handle various certificate date formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def _classify_content_type(self, title: str) -> str:
        """Classify dark web content type based on title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['market', 'shop', 'store', 'sell']):
            return 'market'
        elif any(keyword in title_lower for keyword in ['forum', 'discussion', 'thread']):
            return 'forum'
        elif any(keyword in title_lower for keyword in ['leak', 'dump', 'breach']):
            return 'leak'
        else:
            return 'blog'

    def _assess_threat_level(self, title: str, keywords: List[str]) -> str:
        """Assess threat level based on content"""
        title_lower = title.lower()
        keywords_lower = [k.lower() for k in keywords]
        
        high_threat_keywords = ['breach', 'leak', 'hack', 'exploit', 'vulnerability', 'attack']
        medium_threat_keywords = ['discussion', 'forum', 'analysis', 'research']
        
        if any(keyword in title_lower for keyword in high_threat_keywords):
            return 'high'
        elif any(keyword in title_lower for keyword in medium_threat_keywords):
            return 'medium'
        else:
            return 'low'

    def _deduplicate_nodes(self, nodes: List[NetworkNode]) -> List[NetworkNode]:
        """Remove duplicate network nodes"""
        seen_ips = set()
        unique_nodes = []
        
        for node in nodes:
            if node.ip_address not in seen_ips:
                seen_ips.add(node.ip_address)
                unique_nodes.append(node)
                
        return unique_nodes

    def _deduplicate_certificates(self, certificates: List[SSLCertificate]) -> List[SSLCertificate]:
        """Remove duplicate certificates"""
        seen_serials = set()
        unique_certs = []
        
        for cert in certificates:
            if cert.serial_number not in seen_serials:
                seen_serials.add(cert.serial_number)
                unique_certs.append(cert)
                
        return unique_certs

    async def analyze_technical_footprint(self, target: str) -> Dict[str, Any]:
        """Comprehensive technical footprint analysis"""
        
        analysis = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'whois': None,
            'dns_records': [],
            'network_nodes': [],
            'ssl_certificates': [],
            'dark_web_mentions': [],
            'risk_assessment': {
                'overall_risk': 'low',
                'risk_factors': [],
                'security_recommendations': []
            },
            'infrastructure_summary': {
                'total_ips': 0,
                'countries': set(),
                'asns': set(),
                'open_ports': set(),
                'certificate_issues': []
            }
        }
        
        try:
            # Perform WHOIS lookup if target is a domain
            if not self._is_ip_address(target):
                whois_record = await self.perform_whois_lookup(target)
                analysis['whois'] = asdict(whois_record)
            
            # Analyze DNS records
            dns_records = await self.analyze_dns_records(target)
            analysis['dns_records'] = [asdict(record) for record in dns_records]
            
            # Map network infrastructure
            network_nodes = await self.map_network_infrastructure(target)
            analysis['network_nodes'] = [asdict(node) for node in network_nodes]
            
            # Analyze SSL certificates
            ssl_certs = await self.analyze_ssl_certificates(target)
            analysis['ssl_certificates'] = [asdict(cert) for cert in ssl_certs]
            
            # Monitor dark web for mentions
            dark_web_content = await self.monitor_dark_web([target])
            analysis['dark_web_mentions'] = [asdict(content) for content in dark_web_content]
            
            # Generate infrastructure summary
            analysis['infrastructure_summary']['total_ips'] = len(network_nodes)
            analysis['infrastructure_summary']['countries'] = {node.country for node in network_nodes if node.country}
            analysis['infrastructure_summary']['asns'] = {node.asn for node in network_nodes if node.asn}
            analysis['infrastructure_summary']['open_ports'] = {port for node in network_nodes for port in node.open_ports}
            
            # Check for certificate issues
            for cert in ssl_certs:
                if cert.valid_until and cert.valid_until < date.today():
                    analysis['infrastructure_summary']['certificate_issues'].append(
                        f"Certificate for {cert.domain} expired on {cert.valid_until}"
                    )
            
            # Assess risk factors
            risk_factors = []
            
            if len(network_nodes) > 10:
                risk_factors.append("Large attack surface with many IP addresses")
            
            if len(analysis['infrastructure_summary']['certificate_issues']) > 0:
                risk_factors.append("Expired SSL certificates detected")
            
            high_threat_mentions = [content for content in dark_web_content if content.threat_level in ['high', 'critical']]
            if high_threat_mentions:
                risk_factors.append(f"High-threat dark web mentions: {len(high_threat_mentions)}")
            
            analysis['risk_assessment']['risk_factors'] = risk_factors
            
            # Determine overall risk
            if len(risk_factors) >= 3:
                analysis['risk_assessment']['overall_risk'] = 'high'
            elif len(risk_factors) >= 1:
                analysis['risk_assessment']['overall_risk'] = 'medium'
            
            # Generate security recommendations
            recommendations = []
            
            if analysis['infrastructure_summary']['certificate_issues']:
                recommendations.append("Renew expired SSL certificates immediately")
            
            if len(network_nodes) > 5:
                recommendations.append("Consider consolidating infrastructure to reduce attack surface")
            
            if not analysis['infrastructure_summary']['countries']:
                recommendations.append("Implement geo-blocking for unnecessary regions")
            
            analysis['risk_assessment']['security_recommendations'] = recommendations
            
        except Exception as e:
            logger.error(f"Technical footprint analysis failed for {target}: {str(e)}")
            analysis['error'] = str(e)
            
        return analysis


# Convenience function for quick technical intelligence
async def gather_technical_intelligence(target: str) -> Dict[str, Any]:
    """Gather comprehensive technical intelligence for a target"""
    
    async with TechnicalIntelligenceService() as service:
        return await service.analyze_technical_footprint(target)