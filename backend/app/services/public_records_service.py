"""
Public Records Integration Service
Provides access to government databases, corporate registries, property records, and court documents
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, date
from urllib.parse import urljoin, quote_plus
import logging

from bs4 import BeautifulSoup
from app.services.error_handling import handle_errors, RetryConfig
from app.services.llm_integration import LLMIntegrationService

logger = logging.getLogger(__name__)


@dataclass
class PublicRecord:
    """Base class for public records"""
    record_type: str = ""
    source: str = ""
    title: str = ""
    description: str = ""
    url: Optional[str] = None
    date_accessed: Optional[datetime] = None
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CorporateRecord(PublicRecord):
    """Corporate registration record"""
    company_name: str = ""
    registration_number: str = ""
    incorporation_date: Optional[date] = None
    status: str = "unknown"
    jurisdiction: str = "unknown"
    officers: Optional[List[Dict[str, str]]] = None
    address: Optional[str] = None
    registered_agent: Optional[str] = None
    
    def __post_init__(self):
        if not self.record_type:
            self.record_type = "corporate_registration"
        if not self.description and self.company_name:
            self.description = f"Corporate registration for {self.company_name}"
        if not self.title and self.company_name:
            self.title = f"Company: {self.company_name}"


@dataclass
class PropertyRecord(PublicRecord):
    """Property ownership record"""
    property_address: str = ""
    owner_name: str = ""
    parcel_number: Optional[str] = None
    assessed_value: Optional[float] = None
    property_type: str = "unknown"
    last_sale_date: Optional[date] = None
    last_sale_amount: Optional[float] = None
    tax_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.record_type:
            self.record_type = "property_ownership"
        if not self.description and self.property_address:
            self.description = f"Property ownership for {self.property_address}"
        if not self.title and self.property_address:
            self.title = f"Property: {self.property_address}"


@dataclass
class CourtRecord(PublicRecord):
    """Court case record"""
    case_number: str = ""
    court: str = ""
    case_type: str = ""
    filing_date: Optional[date] = None
    status: str = "unknown"
    parties: Optional[List[str]] = None
    outcome: Optional[str] = None
    charges: Optional[List[str]] = None
    
    def __post_init__(self):
        if not self.record_type:
            self.record_type = "court_case"
        if not self.description and self.case_number:
            self.description = f"Court case {self.case_number}"
        if not self.title and self.case_number:
            self.title = f"Case: {self.case_number}"


@dataclass
class ProfessionalLicense(PublicRecord):
    """Professional license record"""
    licensee_name: str = ""
    license_number: str = ""
    profession: str = ""
    issuing_authority: str = ""
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: str = "unknown"
    disciplinary_actions: Optional[List[str]] = None
    
    def __post_init__(self):
        if not self.record_type:
            self.record_type = "professional_license"
        if not self.description and self.licensee_name:
            self.description = f"Professional license for {self.licensee_name}"
        if not self.title and self.license_number:
            self.title = f"License: {self.license_number}"


class PublicRecordsService:
    """Service for accessing public records from various sources"""
    
    def __init__(self):
        self.llm_service = LLMIntegrationService()
        self.session = None
        self.retry_config = RetryConfig(max_retries=3, base_delay=2.0)
        
        # Government database endpoints
        self.gov_databases = {
            'sec_edgar': 'https://www.sec.gov/Archives/edgar/data/',
            'uspto': 'https://tsedemo.uspto.gov/',
            'fcc_uls': 'https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp',
            'faa_aircraft': 'https://registry.faa.gov/aircraftinquiry/',
            'national_archive': 'https://catalog.archives.gov/',
            'congress_gov': 'https://www.congress.gov/',
            'federal_register': 'https://www.federalregister.gov/',
            'court_pacer': 'https://pacer.uscourts.gov/',
            'uscourts_opinions': 'https://www.uscourts.gov/opinions-opinions',
            'federal_bureau_prisons': 'https://www.bop.gov/inmateloc/',
            'sex_offender_registry': 'https://www.nsopw.gov/',
            'corporations_wiki': 'https://opencorporates.com/',
            'property_assessor_demo': 'https://publicrecords.onlinesearches.com/',
            'professional_licenses_demo': 'https://www.licenseverification.com/'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @handle_errors("public_records", "corporate_search", RetryConfig(max_retries=3, base_delay=2.0))
    async def search_corporate_records(self, company_name: str, jurisdiction: str = "US") -> List[CorporateRecord]:
        """Search corporate registration records"""
        records = []
        
        try:
            # OpenCorporates API (free tier available)
            opencorporates_url = f"https://api.opencorporates.com/companies/search"
            params = {
                'q': company_name,
                'jurisdiction_code': jurisdiction,
                'per_page': 10,
                'order': 'score',
                'registered_address_in': 'US'
            }
            
            async with self.session.get(opencorporates_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for company in data.get('results', {}).get('companies', []):
                        company_data = company.get('company', {})
                        
                        record = CorporateRecord(
                            record_type="corporate_registration",
                            source="OpenCorporates",
                            title=company_data.get('name', ''),
                            description=f"Company registered in {company_data.get('jurisdiction_code', '')}",
                            url=company_data.get('opencorporates_url'),
                            date_accessed=datetime.now(),
                            confidence=0.8,
                            metadata={
                                'company_number': company_data.get('company_number'),
                                'registered_address': company_data.get('registered_address_in_full'),
                                'current_status': company_data.get('current_status'),
                                'incorporation_date': company_data.get('incorporation_date'),
                                'dissolution_date': company_data.get('dissolution_date'),
                                'company_type': company_data.get('company_type'),
                                'registry_url': company_data.get('registry_url')
                            },
                            company_name=company_data.get('name', ''),
                            registration_number=company_data.get('company_number', ''),
                            incorporation_date=self._parse_date(company_data.get('incorporation_date')),
                            status=company_data.get('current_status', 'unknown'),
                            jurisdiction=company_data.get('jurisdiction_code', ''),
                            address=company_data.get('registered_address_in_full'),
                            officers=company_data.get('officers', [])
                        )
                        records.append(record)
            
            # SEC EDGAR search for public companies
            if len(records) < 5:  # Only search SEC if we need more results
                sec_records = await self._search_sec_edgar(company_name)
                records.extend(sec_records)
                
        except Exception as e:
            logger.error(f"Error searching corporate records: {str(e)}")
            
        # Remove duplicates and sort by confidence
        unique_records = self._deduplicate_records(records, 'company_name')
        return sorted(unique_records, key=lambda x: x.confidence, reverse=True)[:10]

    @handle_errors("public_records", "property_search", RetryConfig(max_retries=3, base_delay=2.0))
    async def search_property_records(self, owner_name: str, property_address: str = "") -> List[PropertyRecord]:
        """Search property ownership records"""
        records = []
        
        try:
            # County assessor search (demo with public records aggregator)
            search_query = f"{owner_name}"
            if property_address:
                search_query += f" {property_address}"
                
            # Using public records search sites (these are demo implementations)
            search_urls = [
                f"https://publicrecords.onlinesearches.com/Property_Owner_Search_{quote_plus(owner_name)}.htm",
                f"https://www.countyoffice.org/property-records-{quote_plus(owner_name)}/"
            ]
            
            for url in search_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Parse property records (this is a simplified parser)
                            property_records = self._parse_property_records(soup, owner_name, url)
                            records.extend(property_records)
                            
                            await asyncio.sleep(1)  # Rate limiting
                            
                except Exception as e:
                    logger.debug(f"Failed to search {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching property records: {str(e)}")
            
        # Generate simulated records if no real data found (for development)
        if not records:
            records = await self._generate_demo_property_records(owner_name, property_address)
            
        # Remove duplicates and sort by confidence
        unique_records = self._deduplicate_records(records, 'property_address')
        return sorted(unique_records, key=lambda x: x.confidence, reverse=True)[:10]

    @handle_errors("public_records", "court_search", RetryConfig(max_retries=3, base_delay=2.0))
    async def search_court_records(self, person_name: str, case_type: str = "") -> List[CourtRecord]:
        """Search court case records"""
        records = []
        
        try:
            # PACER Public Access to Court Electronic Records
            # Note: PACER requires registration, so we'll use public court opinion sites
            
            # Search US Courts opinions
            uscourts_url = "https://www.uscourts.gov/opinions-opinions"
            search_params = {
                'keywords': person_name,
                'type': 'published'
            }
            
            async with self.session.get(uscourts_url, params=search_params) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    court_records = self._parse_court_records(soup, person_name, "uscourts")
                    records.extend(court_records)
            
            # Search state court databases (demo implementation)
            state_court_urls = [
                f"https://www.courts.ca.gov/search_people?person={quote_plus(person_name)}",
                f"https://www.nycourts.gov/courthelp/search/person?name={quote_plus(person_name)}"
            ]
            
            for court_url in state_court_urls:
                try:
                    async with self.session.get(court_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            state_records = self._parse_court_records(soup, person_name, "state_court")
                            records.extend(state_records)
                            
                            await asyncio.sleep(1)  # Rate limiting
                            
                except Exception as e:
                    logger.debug(f"Failed to search {court_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching court records: {str(e)}")
            
        # Generate demo records if no real data found
        if not records:
            records = await self._generate_demo_court_records(person_name, case_type)
            
        # Remove duplicates and sort by confidence
        unique_records = self._deduplicate_records(records, 'case_number')
        return sorted(unique_records, key=lambda x: x.confidence, reverse=True)[:10]

    @handle_errors("public_records", "professional_license_search", RetryConfig(max_retries=3, base_delay=2.0))
    async def search_professional_licenses(self, person_name: str, profession: str = "") -> List[ProfessionalLicense]:
        """Search professional license records"""
        records = []
        
        try:
            # Professional license verification sites
            license_boards = {
                'medical': 'https://www.docboard.org/qa/quicksearch.asp',
                'legal': 'https://www.americanbar.org/groups/professional_responsibility/resources/attorney_discipline/', 
                'engineering': 'https://www.nspe.org/resources/ethics/board-of-ethical-review/',
                'real_estate': 'https://www.arec.arkansas.gov/pages/verify-license',
                'accounting': 'https://www.aicpa.org/research/standards/codeofethics/enforcement.html',
                'general': 'https://www.licenseverification.com/'
            }
            
            # Search relevant boards based on profession
            search_urls = []
            if profession.lower() in license_boards:
                search_urls.append(license_boards[profession.lower()])
            search_urls.append(license_boards['general'])
            
            for url in search_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            license_records = self._parse_license_records(soup, person_name, profession, url)
                            records.extend(license_records)
                            
                            await asyncio.sleep(1)  # Rate limiting
                            
                except Exception as e:
                    logger.debug(f"Failed to search {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching professional licenses: {str(e)}")
            
        # Generate demo records if no real data found
        if not records:
            records = await self._generate_demo_license_records(person_name, profession)
            
        # Remove duplicates and sort by confidence
        unique_records = self._deduplicate_records(records, 'license_number')
        return sorted(unique_records, key=lambda x: x.confidence, reverse=True)[:10]

    @handle_errors("public_records", "gov_database_search", RetryConfig(max_retries=3, base_delay=2.0))
    async def search_government_databases(self, search_term: str, database_types: List[str] = None) -> List[PublicRecord]:
        """Search various government databases"""
        if database_types is None:
            database_types = ['sec', 'uspto', 'fcc', 'national_archive']
            
        records = []
        
        for db_type in database_types:
            try:
                if db_type == 'sec':
                    sec_records = await self._search_sec_edgar(search_term)
                    records.extend(sec_records)
                elif db_type == 'uspto':
                    patent_records = await self._search_uspto(search_term)
                    records.extend(patent_records)
                elif db_type == 'fcc':
                    fcc_records = await self._search_fcc_uls(search_term)
                    records.extend(fcc_records)
                elif db_type == 'national_archive':
                    archive_records = await self._search_national_archive(search_term)
                    records.extend(archive_records)
                    
                await asyncio.sleep(1)  # Rate limiting between searches
                
            except Exception as e:
                logger.debug(f"Failed to search {db_type} database: {str(e)}")
                continue
                
        return sorted(records, key=lambda x: x.confidence, reverse=True)[:20]

    async def _search_sec_edgar(self, company_name: str) -> List[CorporateRecord]:
        """Search SEC EDGAR database for company information"""
        records = []
        
        try:
            # SEC EDGAR API
            search_url = "https://www.sec.gov/Archives/edgar/data/"
            
            # First search for company CIK
            cik_search_url = f"https://www.sec.gov/files/edgar/data/company-tickers.json"
            
            async with self.session.get(cik_search_url) as response:
                if response.status == 200:
                    ticker_data = await response.json()
                    
                    # Search for matching company name
                    matching_cik = None
                    for cik, info in ticker_data.values():
                        if company_name.lower() in info.get('title', '').lower():
                            matching_cik = info.get('ticker')
                            break
                    
                    if matching_cik:
                        # Get company information
                        company_url = f"{search_url}{matching_cik}/"
                        
                        record = CorporateRecord(
                            record_type="sec_filing",
                            source="SEC EDGAR",
                            title=company_name,
                            description=f"Public company with SEC filings",
                            url=company_url,
                            date_accessed=datetime.now(),
                            confidence=0.9,
                            metadata={'cik': matching_cik},
                            company_name=company_name,
                            registration_number=matching_cik,
                            status="active",
                            jurisdiction="US"
                        )
                        records.append(record)
                        
        except Exception as e:
            logger.debug(f"SEC EDGAR search failed: {str(e)}")
            
        return records

    async def _search_uspto(self, search_term: str) -> List[PublicRecord]:
        """Search US Patent and Trademark Office database"""
        records = []
        
        try:
            # USPTO Patent Full-Text and Image Database
            search_url = "https://patft.uspto.gov/netacgi/nph-Parser"
            params = {
                'patentnumber': search_term,
                'Sect1': 'PTO1',
                'Sect2': 'HITOFF',
                'u': '/netahtml/PTO/search-adv.htm',
                'r': '0',
                'p': '1',
                'f': 'S',
                'l': '50',
                'd': 'PALL',
                'Query': search_term
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Parse patent results
                    patent_results = soup.find_all('table', class_='patent-result')
                    
                    for result in patent_results[:10]:
                        title_elem = result.find('th')
                        if title_elem:
                            record = PublicRecord(
                                record_type="patent",
                                source="USPTO",
                                title=title_elem.get_text(strip=True),
                                description=f"Patent related to {search_term}",
                                url=f"https://patft.uspto.gov/netacgi/nph-Parser?patentnumber={title_elem.get_text(strip=True)}",
                                date_accessed=datetime.now(),
                                confidence=0.7,
                                metadata={'search_term': search_term}
                            )
                            records.append(record)
                            
        except Exception as e:
            logger.debug(f"USPTO search failed: {str(e)}")
            
        return records

    async def _search_fcc_uls(self, search_term: str) -> List[PublicRecord]:
        """Search FCC Universal Licensing System"""
        records = []
        
        try:
            # FCC ULS search
            search_url = "https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp"
            
            # This is a simplified implementation - real FCC search requires more complex form submission
            params = {
                'licType': 'ALL',
                'searchType': 'LIC',
                'searchValue': search_term
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Parse FCC license results
                    license_results = soup.find_all('tr', class_='result-row')
                    
                    for result in license_results[:10]:
                        cells = result.find_all('td')
                        if len(cells) >= 3:
                            record = PublicRecord(
                                record_type="fcc_license",
                                source="FCC ULS",
                                title=f"FCC License: {cells[0].get_text(strip=True)}",
                                description=f"License for {cells[1].get_text(strip=True)}",
                                url="https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp",
                                date_accessed=datetime.now(),
                                confidence=0.6,
                                metadata={
                                    'call_sign': cells[0].get_text(strip=True),
                                    'licensee': cells[1].get_text(strip=True),
                                    'service': cells[2].get_text(strip=True)
                                }
                            )
                            records.append(record)
                            
        except Exception as e:
            logger.debug(f"FCC ULS search failed: {str(e)}")
            
        return records

    async def _search_national_archive(self, search_term: str) -> List[PublicRecord]:
        """Search National Archives catalog"""
        records = []
        
        try:
            # National Archives API
            search_url = "https://catalog.archives.gov/api/v1/"
            params = {
                'q': search_term,
                'rows': 10
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for doc in data.get('opaResponse', {}).get('results', {}).get('result', []):
                        record = PublicRecord(
                            record_type="national_archive",
                            source="National Archives",
                            title=doc.get('title', {}).get('#text', ''),
                            description=doc.get('description', {}).get('#text', ''),
                            url=f"https://catalog.archives.gov/id/{doc.get('naId', '')}",
                            date_accessed=datetime.now(),
                            confidence=0.8,
                            metadata={
                                'naId': doc.get('naId'),
                                'type': doc.get('type'),
                                'date': doc.get('creationDate')
                            }
                        )
                        records.append(record)
                        
        except Exception as e:
            logger.debug(f"National Archives search failed: {str(e)}")
            
        return records

    def _parse_property_records(self, soup: BeautifulSoup, owner_name: str, source_url: str) -> List[PropertyRecord]:
        """Parse property records from HTML content"""
        records = []
        
        # This is a simplified parser - real implementations would need site-specific parsing
        property_elements = soup.find_all('div', class_='property-record')
        
        for elem in property_elements[:10]:
            try:
                address_elem = elem.find('span', class_='address')
                owner_elem = elem.find('span', class_='owner')
                value_elem = elem.find('span', class_='value')
                
                if address_elem:
                    record = PropertyRecord(
                        record_type="property_ownership",
                        source=source_url,
                        title=f"Property: {address_elem.get_text(strip=True)}",
                        description=f"Property owned by {owner_name}",
                        url=source_url,
                        date_accessed=datetime.now(),
                        confidence=0.6,
                        metadata={'raw_html': str(elem)},
                        property_address=address_elem.get_text(strip=True),
                        owner_name=owner_name,
                        assessed_value=float(value_elem.get_text(strip=True).replace('$', '').replace(',', '')) if value_elem else None
                    )
                    records.append(record)
                    
            except Exception as e:
                logger.debug(f"Error parsing property record: {str(e)}")
                continue
                
        return records

    def _parse_court_records(self, soup: BeautifulSoup, person_name: str, source: str) -> List[CourtRecord]:
        """Parse court records from HTML content"""
        records = []
        
        # Simplified parser for court records
        case_elements = soup.find_all('div', class_='case-record')
        
        for elem in case_elements[:10]:
            try:
                case_number_elem = elem.find('span', class_='case-number')
                court_elem = elem.find('span', class_='court')
                case_type_elem = elem.find('span', class_='case-type')
                
                if case_number_elem:
                    record = CourtRecord(
                        record_type="court_case",
                        source=source,
                        title=f"Case: {case_number_elem.get_text(strip=True)}",
                        description=f"Court case involving {person_name}",
                        url=soup.find('base', href='/')['href'] + case_number_elem.get('href', '') if case_number_elem.get('href') else None,
                        date_accessed=datetime.now(),
                        confidence=0.7,
                        metadata={'raw_html': str(elem)},
                        case_number=case_number_elem.get_text(strip=True),
                        court=court_elem.get_text(strip=True) if court_elem else "Unknown Court",
                        case_type=case_type_elem.get_text(strip=True) if case_type_elem else "Unknown"
                    )
                    records.append(record)
                    
            except Exception as e:
                logger.debug(f"Error parsing court record: {str(e)}")
                continue
                
        return records

    def _parse_license_records(self, soup: BeautifulSoup, person_name: str, profession: str, source_url: str) -> List[ProfessionalLicense]:
        """Parse professional license records from HTML content"""
        records = []
        
        # Simplified parser for license records
        license_elements = soup.find_all('div', class_='license-record')
        
        for elem in license_elements[:10]:
            try:
                license_num_elem = elem.find('span', class_='license-number')
                profession_elem = elem.find('span', class_='profession')
                status_elem = elem.find('span', class_='status')
                
                if license_num_elem:
                    record = ProfessionalLicense(
                        record_type="professional_license",
                        source=source_url,
                        title=f"License: {license_num_elem.get_text(strip=True)}",
                        description=f"Professional license for {person_name}",
                        url=source_url,
                        date_accessed=datetime.now(),
                        confidence=0.8,
                        metadata={'raw_html': str(elem)},
                        licensee_name=person_name,
                        license_number=license_num_elem.get_text(strip=True),
                        profession=profession_elem.get_text(strip=True) if profession_elem else profession,
                        issuing_authority="State Licensing Board",
                        status=status_elem.get_text(strip=True) if status_elem else "unknown"
                    )
                    records.append(record)
                    
            except Exception as e:
                logger.debug(f"Error parsing license record: {str(e)}")
                continue
                
        return records

    async def _generate_demo_property_records(self, owner_name: str, property_address: str) -> List[PropertyRecord]:
        """Generate demo property records for development"""
        records = []
        
        demo_properties = [
            {
                'address': property_address or f"123 Main St, Anytown, USA",
                'value': 350000,
                'type': 'Residential'
            },
            {
                'address': f"456 Oak Ave, Anytown, USA",
                'value': 275000,
                'type': 'Residential'
            }
        ]
        
        for prop in demo_properties:
            record = PropertyRecord(
                record_type="property_ownership",
                source="Demo Data",
                title=f"Property: {prop['address']}",
                description=f"Property owned by {owner_name}",
                url=None,
                date_accessed=datetime.now(),
                confidence=0.3,  # Low confidence for demo data
                metadata={'demo': True},
                property_address=prop['address'],
                owner_name=owner_name,
                assessed_value=prop['value'],
                property_type=prop['type']
            )
            records.append(record)
            
        return records

    async def _generate_demo_court_records(self, person_name: str, case_type: str) -> List[CourtRecord]:
        """Generate demo court records for development"""
        records = []
        
        demo_cases = [
            {
                'number': f"CIV-2024-{hash(person_name) % 10000:04d}",
                'court': "Superior Court",
                'type': case_type or "Civil"
            }
        ]
        
        for case in demo_cases:
            record = CourtRecord(
                record_type="court_case",
                source="Demo Data",
                title=f"Case: {case['number']}",
                description=f"Court case involving {person_name}",
                url=None,
                date_accessed=datetime.now(),
                confidence=0.3,  # Low confidence for demo data
                metadata={'demo': True},
                case_number=case['number'],
                court=case['court'],
                case_type=case['type'],
                parties=[person_name]
            )
            records.append(record)
            
        return records

    async def _generate_demo_license_records(self, person_name: str, profession: str) -> List[ProfessionalLicense]:
        """Generate demo professional license records for development"""
        records = []
        
        demo_licenses = [
            {
                'number': f"LI{hash(person_name) % 100000:06d}",
                'profession': profession or "Professional",
                'authority': "State Board",
                'status': "Active"
            }
        ]
        
        for license_data in demo_licenses:
            record = ProfessionalLicense(
                record_type="professional_license",
                source="Demo Data",
                title=f"License: {license_data['number']}",
                description=f"Professional license for {person_name}",
                url=None,
                date_accessed=datetime.now(),
                confidence=0.3,  # Low confidence for demo data
                metadata={'demo': True},
                licensee_name=person_name,
                license_number=license_data['number'],
                profession=license_data['profession'],
                issuing_authority=license_data['authority'],
                status=license_data['status']
            )
            records.append(record)
            
        return records

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string into date object"""
        if not date_str:
            return None
            
        try:
            # Handle various date formats
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
                    
        except Exception:
            pass
            
        return None

    def _deduplicate_records(self, records: List[PublicRecord], key_field: str) -> List[PublicRecord]:
        """Remove duplicate records based on specified field"""
        seen = set()
        unique_records = []
        
        for record in records:
            key = getattr(record, key_field, None)
            if key and key not in seen:
                seen.add(key)
                unique_records.append(record)
                
        return unique_records

    async def analyze_record_patterns(self, records: List[PublicRecord]) -> Dict[str, Any]:
        """Analyze patterns across multiple records"""
        analysis = {
            'total_records': len(records),
            'record_types': {},
            'sources': {},
            'time_distribution': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'key_insights': []
        }
        
        for record in records:
            # Count record types
            record_type = record.record_type
            analysis['record_types'][record_type] = analysis['record_types'].get(record_type, 0) + 1
            
            # Count sources
            source = record.source
            analysis['sources'][source] = analysis['sources'].get(source, 0) + 1
            
            # Confidence distribution
            if record.confidence >= 0.8:
                analysis['confidence_distribution']['high'] += 1
            elif record.confidence >= 0.5:
                analysis['confidence_distribution']['medium'] += 1
            else:
                analysis['confidence_distribution']['low'] += 1
        
        # Generate insights
        if analysis['total_records'] > 0:
            most_common_type = max(analysis['record_types'], key=analysis['record_types'].get)
            analysis['key_insights'].append(f"Most common record type: {most_common_type}")
            
            if analysis['confidence_distribution']['high'] > 0:
                high_conf_pct = (analysis['confidence_distribution']['high'] / analysis['total_records']) * 100
                analysis['key_insights'].append(f"{high_conf_pct:.1f}% of records are high confidence")
        
        return analysis


# Convenience function for quick public records search
async def search_public_records(query: str, record_types: List[str] = None) -> Dict[str, List[PublicRecord]]:
    """Search all public records for a query"""
    if record_types is None:
        record_types = ['corporate', 'property', 'court', 'license']
        
    results = {}
    
    async with PublicRecordsService() as service:
        if 'corporate' in record_types:
            results['corporate'] = await service.search_corporate_records(query)
            
        if 'property' in record_types:
            results['property'] = await service.search_property_records(query)
            
        if 'court' in record_types:
            results['court'] = await service.search_court_records(query)
            
        if 'license' in record_types:
            results['license'] = await service.search_professional_licenses(query)
            
        # Government databases
        gov_results = await service.search_government_databases(query)
        results['government'] = gov_results
        
        # Analyze patterns
        all_records = []
        for record_list in results.values():
            all_records.extend(record_list)
            
        results['analysis'] = await service.analyze_record_patterns(all_records)
        
    return results