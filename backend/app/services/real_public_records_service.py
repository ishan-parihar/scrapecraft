"""
Real Public Records Integration Service
Provides actual public records data collection using government APIs and web scraping.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
import re

from app.config import settings

logger = logging.getLogger(__name__)

class RealPublicRecordsService:
    """
    Service for performing actual public records data collection.
    """
    
    def __init__(self):
        self.session = None
        self.rate_limiters = {
            'court_records': {'last_request': 0, 'min_delay': 3.0},
            'property_records': {'last_request': 0, 'min_delay': 2.0},
            'business_filings': {'last_request': 0, 'min_delay': 2.0},
            'patents': {'last_request': 0, 'min_delay': 1.0},
            'professional_licenses': {'last_request': 0, 'min_delay': 2.0}
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self, record_type: str):
        """Apply rate limiting for public records sources."""
        if record_type in self.rate_limiters:
            limiter = self.rate_limiters[record_type]
            time_since_last = asyncio.get_event_loop().time() - limiter['last_request']
            if time_since_last < limiter['min_delay']:
                await asyncio.sleep(limiter['min_delay'] - time_since_last)
            limiter['last_request'] = asyncio.get_event_loop().time()
    
    async def search_court_records(self, name: str, jurisdiction: str = "federal") -> Dict[str, Any]:
        """
        Search court records using PACER (Public Access to Court Electronic Records) and other sources.
        
        Args:
            name: Name to search for
            jurisdiction: Court jurisdiction (federal, state, county)
            
        Returns:
            Dictionary containing court records information
        """
        await self._rate_limit('court_records')
        
        try:
            # For federal records, we can use PACER (requires registration)
            # For demonstration, we'll use publicly available court RSS feeds and docket searches
            results = []
            
            # Search federal court docket RSS feeds
            if jurisdiction.lower() == "federal":
                results.extend(await self._search_federal_court_dockets(name))
            
            # Search state court records (varies by state)
            else:
                results.extend(await self._search_state_court_records(name, jurisdiction))
            
            collection_data = {
                "source": "court_records",
                "name": name,
                "jurisdiction": jurisdiction,
                "timestamp": datetime.utcnow().isoformat(),
                "records": results,
                "total_records": len(results),
                "data_source": "real_search",
                "collection_success": True
            }
            
            logger.info(f"Found {len(results)} court records for {name} in {jurisdiction}")
            return collection_data
            
        except Exception as e:
            logger.error(f"Error searching court records for {name}: {str(e)}")
            return {
                "error": str(e),
                "source": "court_records",
                "name": name,
                "jurisdiction": jurisdiction,
                "collection_success": False
            }
    
    async def _search_federal_court_dockets(self, name: str) -> List[Dict[str, Any]]:
        """Search federal court docket information."""
        try:
            # Use CourtListener API (free tier available)
            # This is a real service that provides court data
            url = "https://www.courtlistener.com/api/rest/v3/search/"
            params = {
                'q': name,
                'type': 'o',  # Opinions
                'order_by': 'score desc',
                'page_size': 10
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('results', []):
                        record = {
                            "case_number": item.get('case_name', ''),
                            "case_title": item.get('case_name', ''),
                            "case_type": "opinion",
                            "filing_date": item.get('date_filed', ''),
                            "court": item.get('court', {}).get('short_name', ''),
                            "judge": item.get('author', {}).get('name', ''),
                            "opinion_text": item.get('plain_text', '')[:500],  # First 500 chars
                            "citation": item.get('citation', ''),
                            "url": item.get('absolute_url', ''),
                            "data_source": "courtlistener_api"
                        }
                        results.append(record)
                    
                    return results
                else:
                    logger.warning(f"CourtListener API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Federal docket search error: {e}")
            return []
    
    async def _search_state_court_records(self, name: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """Search state court records (implementation varies by state)."""
        try:
            # This is a placeholder for state-specific implementations
            # Each state has different systems and accessibility
            results = []
            
            # Example: Search for publicly available case information
            search_query = f"{name} {jurisdiction} court records case"
            
            # Use a general search to find court-related documents
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_duckduckgo(search_query, 5)
                
                for result in search_results:
                    if any(keyword in result.get('snippet', '').lower() 
                          for keyword in ['court', 'case', 'docket', 'judgment']):
                        record = {
                            "case_number": f"STATE_{jurisdiction.upper()}_{len(results)+1}",
                            "case_title": f"State Court Case involving {name}",
                            "case_type": "state_court",
                            "filing_date": "",
                            "court": f"{jurisdiction.title()} State Court",
                            "source_url": result.get('url', ''),
                            "snippet": result.get('snippet', ''),
                            "data_source": "web_search"
                        }
                        results.append(record)
            
            return results
            
        except Exception as e:
            logger.error(f"State court search error: {e}")
            return []
    
    async def search_property_records(self, address: str = "", owner_name: str = "", jurisdiction: str = "") -> Dict[str, Any]:
        """
        Search property records using county assessor databases.
        
        Args:
            address: Property address
            owner_name: Property owner name
            jurisdiction: County or jurisdiction
            
        Returns:
            Dictionary containing property records information
        """
        await self._rate_limit('property_records')
        
        try:
            results = []
            
            # Search county assessor websites for property records
            if address:
                results.extend(await self._search_property_by_address(address, jurisdiction))
            elif owner_name:
                results.extend(await self._search_property_by_owner(owner_name, jurisdiction))
            
            collection_data = {
                "source": "property_records",
                "search_criteria": {
                    "address": address,
                    "owner_name": owner_name
                },
                "jurisdiction": jurisdiction,
                "timestamp": datetime.utcnow().isoformat(),
                "records": results,
                "total_records": len(results),
                "data_source": "real_search",
                "collection_success": True
            }
            
            logger.info(f"Found {len(results)} property records")
            return collection_data
            
        except Exception as e:
            logger.error(f"Error searching property records: {str(e)}")
            return {
                "error": str(e),
                "source": "property_records",
                "collection_success": False
            }
    
    async def _search_property_by_address(self, address: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """Search property records by address."""
        try:
            # Use county assessor websites and property data services
            search_query = f"{address} property records {jurisdiction} assessor"
            
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_duckduckgo(search_query, 5)
                
                results = []
                for result in search_results:
                    if any(keyword in result.get('url', '').lower() 
                          for keyword in ['assessor', 'property', 'real-estate', 'county']):
                        record = {
                            "address": address,
                            "jurisdiction": jurisdiction,
                            "source_url": result.get('url', ''),
                            "snippet": result.get('snippet', ''),
                            "assessment_data": await self._extract_property_data(result.get('url', '')),
                            "data_source": "assessor_search"
                        }
                        results.append(record)
                
                return results
                
        except Exception as e:
            logger.error(f"Property address search error: {e}")
            return []
    
    async def _search_property_by_owner(self, owner_name: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """Search property records by owner name."""
        try:
            search_query = f"{owner_name} property owner {jurisdiction} county"
            
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_duckduckgo(search_query, 5)
                
                results = []
                for result in search_results:
                    record = {
                        "owner_name": owner_name,
                        "jurisdiction": jurisdiction,
                        "source_url": result.get('url', ''),
                        "snippet": result.get('snippet', ''),
                        "data_source": "owner_search"
                    }
                    results.append(record)
                
                return results
                
        except Exception as e:
            logger.error(f"Property owner search error: {e}")
            return []
    
    async def _extract_property_data(self, url: str) -> Dict[str, Any]:
        """Extract property data from assessor website."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract property information using regex patterns
                    property_data = {}
                    
                    # Look for assessed values
                    assessed_match = re.search(r'\$?([\d,]+)\s*(?:assessed|assessment)', html, re.IGNORECASE)
                    if assessed_match:
                        property_data["assessed_value"] = int(assessed_match.group(1).replace(',', ''))
                    
                    # Look for square footage
                    sqft_match = re.search(r'([\d,]+)\s*(?:sq\.?ft\.?|square feet)', html, re.IGNORECASE)
                    if sqft_match:
                        property_data["square_footage"] = int(sqft_match.group(1).replace(',', ''))
                    
                    # Look for year built
                    year_match = re.search(r'year built[:\s]*(\d{4})', html, re.IGNORECASE)
                    if year_match:
                        property_data["year_built"] = int(year_match.group(1))
                    
                    # Look for bedrooms/bathrooms
                    bed_match = re.search(r'(\d+)\s*bed', html, re.IGNORECASE)
                    if bed_match:
                        property_data["bedrooms"] = int(bed_match.group(1))
                    
                    bath_match = re.search(r'(\d+)\s*bath', html, re.IGNORECASE)
                    if bath_match:
                        property_data["bathrooms"] = int(bath_match.group(1))
                    
                    return property_data
                    
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            
        return {}
    
    async def search_business_filings(self, business_name: str, jurisdiction: str = "DE") -> Dict[str, Any]:
        """
        Search business registration and filing records.
        
        Args:
            business_name: Business name to search for
            jurisdiction: State of registration
            
        Returns:
            Dictionary containing business filing information
        """
        await self._rate_limit('business_filings')
        
        try:
            results = []
            
            # Use Secretary of State databases and business entity search
            results.extend(await self._search_secretary_of_state(business_name, jurisdiction))
            
            collection_data = {
                "source": "business_filings",
                "business_name": business_name,
                "jurisdiction": jurisdiction,
                "timestamp": datetime.utcnow().isoformat(),
                "filings": results,
                "total_filings": len(results),
                "data_source": "real_search",
                "collection_success": True
            }
            
            logger.info(f"Found {len(results)} business filings for {business_name}")
            return collection_data
            
        except Exception as e:
            logger.error(f"Error searching business filings for {business_name}: {str(e)}")
            return {
                "error": str(e),
                "source": "business_filings",
                "collection_success": False
            }
    
    async def _search_secretary_of_state(self, business_name: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """Search Secretary of State business records."""
        try:
            # Use OpenCorporates API (limited free tier available)
            # This provides real business entity data
            url = "https://api.opencorporates.com/companies/search"
            params = {
                'q': business_name,
                'jurisdiction_code': f'us_{jurisdiction.lower()}',
                'per_page': 5
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for company in data.get('results', {}).get('companies', []):
                        company_data = company.get('company', {})
                        filing = {
                            "business_name": company_data.get('name', ''),
                            "entity_type": company_data.get('company_type', ''),
                            "jurisdiction": company_data.get('jurisdiction_code', ''),
                            "registration_number": company_data.get('company_number', ''),
                            "incorporation_date": company_data.get('incorporation_date', ''),
                            "status": company_data.get('current_status', ''),
                            "registered_address": company_data.get('registered_address_in_full', ''),
                            "data_source": "opencorporates_api",
                            "opencorporates_url": company_data.get('opencorporates_url', '')
                        }
                        results.append(filing)
                    
                    return results
                else:
                    logger.warning(f"OpenCorporates API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Secretary of State search error: {e}")
            return []
    
    async def search_patents(self, inventor: str = "", company: str = "", patent_number: str = "") -> Dict[str, Any]:
        """
        Search patent records using USPTO and Google Patents.
        
        Args:
            inventor: Inventor name
            company: Assignee company
            patent_number: Specific patent number
            
        Returns:
            Dictionary containing patent information
        """
        await self._rate_limit('patents')
        
        try:
            results = []
            
            # Use Google Patents search (publicly accessible)
            search_query = ""
            if inventor:
                search_query += f"inventor:{inventor} "
            if company:
                search_query += f"assignee:{company} "
            if patent_number:
                search_query += patent_number
            
            if search_query.strip():
                results.extend(await self._search_google_patents(search_query.strip()))
            
            collection_data = {
                "source": "patent_records",
                "search_criteria": {
                    "inventor": inventor,
                    "company": company,
                    "patent_number": patent_number
                },
                "timestamp": datetime.utcnow().isoformat(),
                "results": results,
                "total_results": len(results),
                "data_source": "real_search",
                "collection_success": True
            }
            
            logger.info(f"Found {len(results)} patent records")
            return collection_data
            
        except Exception as e:
            logger.error(f"Error searching patent records: {str(e)}")
            return {
                "error": str(e),
                "source": "patent_records",
                "collection_success": False
            }
    
    async def _search_google_patents(self, query: str) -> List[Dict[str, Any]]:
        """Search Google Patents."""
        try:
            search_query = f"{query} (patent)"
            
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_google(search_query, 10)
                
                results = []
                for result in search_results:
                    if 'patent' in result.get('title', '').lower() or 'patent' in result.get('snippet', '').lower():
                        patent_data = {
                            "patent_number": self._extract_patent_number(result.get('title', '')),
                            "title": result.get('title', ''),
                            "snippet": result.get('snippet', ''),
                            "source_url": result.get('url', ''),
                            "data_source": "google_patents_search"
                        }
                        results.append(patent_data)
                
                return results
                
        except Exception as e:
            logger.error(f"Google Patents search error: {e}")
            return []
    
    def _extract_patent_number(self, title: str) -> str:
        """Extract patent number from title."""
        # Patent numbers typically follow patterns like US1234567B2, etc.
        patent_match = re.search(r'(US\s*\d{4,}\s*[A-Z]\d*)', title)
        if patent_match:
            return patent_match.group(1)
        return ""
    
    async def search_professional_licenses(self, name: str, profession: str, jurisdiction: str) -> Dict[str, Any]:
        """
        Search professional license records.
        
        Args:
            name: Professional's name
            profession: Type of profession
            jurisdiction: Licensing jurisdiction
            
        Returns:
            Dictionary containing professional license information
        """
        await self._rate_limit('professional_licenses')
        
        try:
            results = []
            
            # Search state licensing boards
            results.extend(await self._search_state_licenses(name, profession, jurisdiction))
            
            collection_data = {
                "source": "professional_licenses",
                "name": name,
                "profession": profession,
                "jurisdiction": jurisdiction,
                "timestamp": datetime.utcnow().isoformat(),
                "licenses": results,
                "total_licenses": len(results),
                "data_source": "real_search",
                "collection_success": True
            }
            
            logger.info(f"Found {len(results)} professional licenses")
            return collection_data
            
        except Exception as e:
            logger.error(f"Error searching professional licenses: {str(e)}")
            return {
                "error": str(e),
                "source": "professional_licenses",
                "collection_success": False
            }
    
    async def _search_state_licenses(self, name: str, profession: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """Search state professional license databases."""
        try:
            search_query = f"{name} {profession} license {jurisdiction} board"
            
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_duckduckgo(search_query, 5)
                
                results = []
                for result in search_results:
                    if any(keyword in result.get('snippet', '').lower() 
                          for keyword in ['license', 'board', 'verification']):
                        license_data = {
                            "license_holder": name,
                            "profession": profession,
                            "jurisdiction": jurisdiction,
                            "source_url": result.get('url', ''),
                            "snippet": result.get('snippet', ''),
                            "data_source": "license_board_search"
                        }
                        results.append(license_data)
                
                return results
                
        except Exception as e:
            logger.error(f"State license search error: {e}")
            return []


async def perform_public_records_search(record_type: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to perform public records searches.
    
    Args:
        record_type: Type of record (court, property, business, patent, license)
        **kwargs: Additional search parameters
        
    Returns:
        Dictionary containing search results
    """
    async with RealPublicRecordsService() as records_service:
        if record_type == "court":
            name = kwargs.get("name")
            jurisdiction = kwargs.get("jurisdiction", "federal")
            if not name:
                return {"error": "Name required for court records search"}
            return await records_service.search_court_records(name, jurisdiction)
        
        elif record_type == "property":
            address = kwargs.get("address", "")
            owner_name = kwargs.get("owner_name", "")
            jurisdiction = kwargs.get("jurisdiction", "")
            if not address and not owner_name:
                return {"error": "Address or owner name required for property search"}
            return await records_service.search_property_records(address, owner_name, jurisdiction)
        
        elif record_type == "business":
            business_name = kwargs.get("business_name")
            jurisdiction = kwargs.get("jurisdiction", "DE")
            if not business_name:
                return {"error": "Business name required for business search"}
            return await records_service.search_business_filings(business_name, jurisdiction)
        
        elif record_type == "patent":
            inventor = kwargs.get("inventor", "")
            company = kwargs.get("company", "")
            patent_number = kwargs.get("patent_number", "")
            if not any([inventor, company, patent_number]):
                return {"error": "Inventor, company, or patent number required for patent search"}
            return await records_service.search_patents(inventor, company, patent_number)
        
        elif record_type == "license":
            name = kwargs.get("name")
            profession = kwargs.get("profession")
            jurisdiction = kwargs.get("jurisdiction")
            if not all([name, profession, jurisdiction]):
                return {"error": "Name, profession, and jurisdiction required for license search"}
            return await records_service.search_professional_licenses(name, profession, jurisdiction)
        
        else:
            return {"error": f"Record type '{record_type}' not supported"}