"""
Public Records Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from ...base.osint_agent import LLMOSINTAgent, AgentConfig



class PublicRecordsCollectorAgent(LLMOSINTAgent):
    """
    Agent responsible for collecting information from public records.
    Handles government databases, court records, property records, business filings, etc.
    """

    def __init__(self, agent_id: str = "public_records_collector", tools: Optional[List] = None):
        config = AgentConfig(
            agent_id=agent_id,
            role="Public Records Collector",
            description="Collects information from public records including court records, property records, business filings, and government databases"
        )
        # Dynamically import the tool manager classes to avoid import issues
        import importlib.util
        import os
        
        # Import the tool module dynamically
        tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'agents', 'tools', 'langchain_tools.py')
        spec = importlib.util.spec_from_file_location("langchain_tools", tool_module_path)
        if spec is not None and spec.loader is not None:
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            ToolManager = tool_module.ToolManager
            get_global_tool_manager = tool_module.get_global_tool_manager
        else:
            raise ImportError("Could not load langchain tools module")
        
        super().__init__(config=config, tools=tools)
        self.tool_manager = ToolManager() if not tools else get_global_tool_manager()
        
        self.supported_record_types = [
            "court_records", "property_records", "business_filings",
            "voter_registration", "professional_licenses", "tax_records",
            "immigration_records", "corporate_documents", "patents",
            "trademarks", "birth_death_marriage", "criminal_records"
        ]
        self.request_delay = 3.0  # Longer delay for government databases
    
    async def use_web_scraper(self, website_url: str, user_prompt: str) -> Dict[str, Any]:
        """
        Use the web scraper tool to extract data from a specific website.
        
        Args:
            website_url: The URL of the website to scrape
            user_prompt: Natural language prompt describing what data to extract
            
        Returns:
            Dictionary containing the scraped data
        """
        self.logger.info(f"Using web scraper on {website_url} with prompt: {user_prompt}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "smart_scraper",
                website_url=website_url,
                user_prompt=user_prompt
            )
            self.logger.info(f"Web scraper result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error using web scraper: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_web_crawler(self, website_url: str, user_prompt: str, max_depth: int = 2, max_pages: int = 5) -> Dict[str, Any]:
        """
        Use the web crawler tool to crawl and extract data from a website.
        
        Args:
            website_url: The starting URL for crawling
            user_prompt: Natural language prompt describing what data to extract
            max_depth: Maximum crawl depth (default: 2)
            max_pages: Maximum number of pages to crawl (default: 5)
            
        Returns:
            Dictionary containing the crawled data
        """
        self.logger.info(f"Using web crawler starting at {website_url}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "smart_crawler",
                website_url=website_url,
                user_prompt=user_prompt,
                max_depth=max_depth,
                max_pages=max_pages
            )
            self.logger.info(f"Web crawler result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error using web crawler: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_search_tool(self, search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Use the search tool to find relevant websites for public records.
        
        Args:
            search_query: The search query to find relevant websites
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            Dictionary containing search results
        """
        self.logger.info(f"Performing search for: {search_query}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "search_scraper",
                search_query=search_query,
                max_results=max_results
            )
            self.logger.info(f"Search result count: {result.get('count', 0)}")
            return result
        except Exception as e:
            self.logger.error(f"Error using search tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_markdown_converter(self, website_url: str) -> Dict[str, Any]:
        """
        Convert a website to markdown format for easier processing.
        
        Args:
            website_url: The URL of the website to convert to markdown
            
        Returns:
            Dictionary containing the markdown content
        """
        self.logger.info(f"Converting {website_url} to markdown")
        
        try:
            result = await self.tool_manager.execute_tool(
                "markdownify",
                website_url=website_url
            )
            self.logger.info(f"Markdown conversion result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error converting to markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def search_court_records(
        self, 
        name: str, 
        jurisdiction: str,
        case_type: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Search court records for a specific name using real data sources.

        Args:
            name: Name to search for
            jurisdiction: Court jurisdiction (state, county, federal)
            case_type: Optional case type filter
            date_range: Optional date range for search

        Returns:
            Dictionary containing court records information
        """
        self.logger.info(f"Searching court records for {name} in {jurisdiction}")

        try:
            # Use real public records service
            from ....services.real_public_records_service import perform_public_records_search
            
            records_result = await perform_public_records_search(
                record_type="court",
                name=name,
                jurisdiction=jurisdiction
            )
            
            if "error" not in records_result:
                records = records_result.get("records", [])
                # Apply additional filtering if specified
                if case_type:
                    records = [r for r in records if case_type.lower() in r.get("case_type", "").lower()]
                
                if date_range:
                    records = self._filter_records_by_date(records, date_range)
            else:
                records = []

            collection_data = {
                "source": "court_records",
                "name": name,
                "jurisdiction": jurisdiction,
                "case_type": case_type,
                "date_range": date_range,
                "timestamp": time.time(),
                "records": records,
                "total_records": len(records),
                "collection_success": "error" not in records_result,
                "data_source": "real_api"
            }

            self.logger.info(f"Found {len(records)} court records for {name}")
            return collection_data

        except Exception as e:
            self.logger.error(f"Error searching court records for {name}: {str(e)}")
            return {
                "error": str(e),
                "source": "court_records",
                "name": name,
                "jurisdiction": jurisdiction,
                "collection_success": False
            }

    async def search_property_records(
        self, 
        address: Optional[str] = None,
        owner_name: Optional[str] = None,
        parcel_id: Optional[str] = None,
        jurisdiction: str = ""
    ) -> Dict[str, Any]:
        """
        Search property records using real data sources.

        Args:
            address: Property address
            owner_name: Property owner name
            parcel_id: Parcel identification number
            jurisdiction: Geographic jurisdiction

        Returns:
            Dictionary containing property records information
        """
        search_criteria = address or owner_name or parcel_id
        self.logger.info(f"Searching property records for: {search_criteria}")

        try:
            # Use real public records service
            from ....services.real_public_records_service import perform_public_records_search
            
            records_result = await perform_public_records_search(
                record_type="property",
                address=address or "",
                owner_name=owner_name or "",
                jurisdiction=jurisdiction
            )
            
            if "error" not in records_result:
                records = records_result.get("records", [])
                # Filter by parcel ID if specified
                if parcel_id:
                    records = [r for r in records if parcel_id.lower() in str(r).lower()]
            else:
                records = []

            collection_data = {
                "source": "property_records",
                "search_criteria": {
                    "address": address,
                    "owner_name": owner_name,
                    "parcel_id": parcel_id
                },
                "jurisdiction": jurisdiction,
                "timestamp": time.time(),
                "records": records,
                "total_records": len(records),
                "collection_success": "error" not in records_result,
                "data_source": "real_api"
            }

            self.logger.info(f"Found {len(records)} property records")
            return collection_data

        except Exception as e:
            self.logger.error(f"Error searching property records: {str(e)}")
            return {
                "error": str(e),
                "source": "property_records",
                "search_criteria": search_criteria,
                "collection_success": False
            }

    async def search_business_filings(
        self, 
        business_name: str,
        jurisdiction: str,
        filing_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search business registration and filing records using real data sources.

        Args:
            business_name: Business name to search for
            jurisdiction: State or jurisdiction of registration
            filing_type: Type of filing (articles, annual reports, etc.)

        Returns:
            Dictionary containing business filing information
        """
        self.logger.info(f"Searching business filings for {business_name} in {jurisdiction}")

        try:
            # Use real public records service
            from ....services.real_public_records_service import perform_public_records_search
            
            filings_result = await perform_public_records_search(
                record_type="business",
                business_name=business_name,
                jurisdiction=jurisdiction
            )
            
            if "error" not in filings_result:
                filings = filings_result.get("filings", [])
                # Filter by filing type if specified
                if filing_type:
                    filings = [f for f in filings if filing_type.lower() in f.get("filing_type", "").lower()]
            else:
                filings = []

            collection_data = {
                "source": "business_filings",
                "business_name": business_name,
                "jurisdiction": jurisdiction,
                "filing_type": filing_type,
                "timestamp": time.time(),
                "filings": filings,
                "total_filings": len(filings),
                "collection_success": "error" not in filings_result,
                "data_source": "real_api"
            }

            self.logger.info(f"Found {len(filings)} business filings for {business_name}")
            return collection_data

        except Exception as e:
            self.logger.error(f"Error searching business filings for {business_name}: {str(e)}")
            return {
                "error": str(e),
                "source": "business_filings",
                "business_name": business_name,
                "collection_success": False
            }

    async def search_professional_licenses(
        self, 
        name: str,
        profession: str,
        jurisdiction: str,
        license_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search professional license records using real data sources.

        Args:
            name: Professional's name
            profession: Type of profession
            jurisdiction: Licensing jurisdiction
            license_number: Specific license number if known

        Returns:
            Dictionary containing professional license information
        """
        self.logger.info(f"Searching {profession} licenses for {name} in {jurisdiction}")

        try:
            # Use real public records service
            from ....services.real_public_records_service import perform_public_records_search
            
            licenses_result = await perform_public_records_search(
                record_type="license",
                name=name,
                profession=profession,
                jurisdiction=jurisdiction
            )
            
            if "error" not in licenses_result:
                licenses = licenses_result.get("licenses", [])
                # Filter by license number if specified
                if license_number:
                    licenses = [l for l in licenses if license_number.lower() in str(l).lower()]
            else:
                licenses = []

            collection_data = {
                "source": "professional_licenses",
                "name": name,
                "profession": profession,
                "jurisdiction": jurisdiction,
                "license_number": license_number,
                "timestamp": time.time(),
                "licenses": licenses,
                "total_licenses": len(licenses),
                "collection_success": "error" not in licenses_result,
                "data_source": "real_api"
            }

            self.logger.info(f"Found {len(licenses)} professional licenses")
            return collection_data

        except Exception as e:
            self.logger.error(f"Error searching professional licenses: {str(e)}")
            return {
                "error": str(e),
                "source": "professional_licenses",
                "name": name,
                "profession": profession,
                "collection_success": False
            }

    async def search_patent_trademarks(
        self, 
        name: Optional[str] = None,
        company: Optional[str] = None,
        patent_number: Optional[str] = None,
        trademark_name: Optional[str] = None,
        search_type: str = "both"
    ) -> Dict[str, Any]:
        """
        Search patent and trademark records using real data sources.

        Args:
            name: Inventor or owner name
            company: Company name
            patent_number: Specific patent number
            trademark_name: Trademark name
            search_type: Type of search ("patents", "trademarks", "both")

        Returns:
            Dictionary containing patent and trademark information
        """
        self.logger.info(f"Searching patents/trademarks for: {name or company or patent_number}")

        try:
            # Use real public records service for patents
            from ....services.real_public_records_service import perform_public_records_search
            
            patents_result = await perform_public_records_search(
                record_type="patent",
                inventor=name or "",
                company=company or "",
                patent_number=patent_number or ""
            )
            
            if "error" not in patents_result:
                results = patents_result.get("results", [])
            else:
                results = []

            collection_data = {
                "source": "patent_trademark_records",
                "search_criteria": {
                    "name": name,
                    "company": company,
                    "patent_number": patent_number,
                    "trademark_name": trademark_name
                },
                "search_type": search_type,
                "timestamp": time.time(),
                "results": results,
                "total_results": len(results),
                "collection_success": "error" not in patents_result,
                "data_source": "real_api"
            }

            self.logger.info(f"Found {len(results)} patent/trademark records")
            return collection_data

        except Exception as e:
            self.logger.error(f"Error searching patent/trademark records: {str(e)}")
            return {
                "error": str(e),
                "source": "patent_trademark_records",
                "collection_success": False
            }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a public records collection task.

        Args:
            task: Task dictionary containing collection parameters

        Returns:
            Dictionary containing collection results
        """
        task_type = task.get("task_type", "court_records")
        
        # Handle LangChain tool-based tasks
        if task_type == "langchain_tool":
            return await self._execute_langchain_tool_task(task)
        
        # Handle traditional collection tasks
        results = []

        if task_type == "court_records":
            # Court records search
            searches = task.get("searches", [])
            for search in searches:
                name = search.get("name")
                jurisdiction = search.get("jurisdiction")
                if name and jurisdiction:
                    result = await self.search_court_records(
                        name, jurisdiction,
                        search.get("case_type"),
                        search.get("date_range")
                    )
                    results.append(result)
                    await asyncio.sleep(self.request_delay)

        elif task_type == "property_records":
            # Property records search
            searches = task.get("searches", [])
            for search in searches:
                result = await self.search_property_records(
                    search.get("address"),
                    search.get("owner_name"),
                    search.get("parcel_id"),
                    search.get("jurisdiction", "")
                )
                results.append(result)
                await asyncio.sleep(self.request_delay)

        elif task_type == "business_filings":
            # Business filings search
            searches = task.get("searches", [])
            for search in searches:
                business_name = search.get("business_name")
                jurisdiction = search.get("jurisdiction")
                if business_name and jurisdiction:
                    result = await self.search_business_filings(
                        business_name, jurisdiction,
                        search.get("filing_type")
                    )
                    results.append(result)
                    await asyncio.sleep(self.request_delay)

        elif task_type == "professional_licenses":
            # Professional licenses search
            searches = task.get("searches", [])
            for search in searches:
                name = search.get("name")
                profession = search.get("profession")
                jurisdiction = search.get("jurisdiction")
                if name and profession and jurisdiction:
                    result = await self.search_professional_licenses(
                        name, profession, jurisdiction,
                        search.get("license_number")
                    )
                    results.append(result)
                    await asyncio.sleep(self.request_delay)

        elif task_type == "patent_trademarks":
            # Patent and trademark search
            searches = task.get("searches", [])
            for search in searches:
                result = await self.search_patent_trademarks(
                    search.get("name"),
                    search.get("company"),
                    search.get("patent_number"),
                    search.get("trademark_name"),
                    search.get("search_type", "both")
                )
                results.append(result)
                await asyncio.sleep(self.request_delay)

        return {
            "agent_id": self.config.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_collections": len(results),
            "status": "completed"
        }
     
    async def _execute_langchain_tool_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a LangChain tool-based task.

        Args:
            task: Task dictionary containing tool execution parameters

        Returns:
            Dictionary containing tool execution results
        """
        tool_name = task.get("tool_name")
        tool_args = task.get("tool_args", {})
        
        if not tool_name:
            return {
                "success": False,
                "error": "Tool name not specified in task",
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "failed"
            }
        
        self.logger.info(f"Executing LangChain tool: {tool_name} with args: {tool_args}")
        
        try:
            result = await self.tool_manager.execute_tool(tool_name, **tool_args)
            return {
                "success": result.get("success", False),
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": result,
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"Error executing LangChain tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_args": tool_args,
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "failed"
            }

    def _filter_records_by_date(self, records: List[Dict[str, Any]], date_range: Dict[str, str]) -> List[Dict[str, Any]]:
        """Filter records by date range."""
        try:
            from datetime import datetime
            
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            
            filtered_records = []
            for record in records:
                # Look for date fields in various formats
                record_date = None
                date_fields = ["filing_date", "date_filed", "creation_date", "timestamp", "date"]
                
                for field in date_fields:
                    if field in record and record[field]:
                        try:
                            date_str = str(record[field])
                            # Handle different date formats
                            if len(date_str) == 10 and date_str.count('-') == 2:  # YYYY-MM-DD
                                record_date = datetime.strptime(date_str, '%Y-%m-%d')
                            elif 'T' in date_str:  # ISO format
                                record_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                # Try to parse other common formats
                                record_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                
                if not record_date:
                    continue
                
                # Apply date filters
                if start_date:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    if record_date < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    if record_date > end_dt:
                        continue
                
                filtered_records.append(record)
            
            return filtered_records
            
        except Exception as e:
            self.logger.error(f"Date filtering failed: {e}")
            return records

    def _generate_date(self, days_ago: int) -> str:
        """Generate date string for days ago."""
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")

    def _generate_future_date(self, days_ahead: int) -> str:
        """Generate future date string."""
        date = datetime.now() + timedelta(days=days_ahead)
        return date.strftime("%Y-%m-%d")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """
        You are an expert Public Records Collector AI assistant. Your role is to collect information 
        from public records including court records, property records, business filings, and government databases.

        When given a request, you should:
        1. Identify the specific type of public record needed
        2. Determine the appropriate search parameters
        3. Execute the search using the available tools
        4. Return structured results in the appropriate format
        5. Always prioritize accuracy and relevance

        Available record types: court_records, property_records, business_filings, 
        voter_registration, professional_licenses, tax_records, immigration_records, 
        corporate_documents, patents, trademarks, birth_death_marriage, criminal_records
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process the LLM response and extract structured output."""
        # For now, return the raw response - in a real implementation,
        # this would parse the LLM response into structured data
        return {"raw_response": raw_output}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data before processing."""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)

    async def collect_public_records_data(self, target: str) -> Dict[str, Any]:
        """
        Collect public records data for a target.
        
        Args:
            target: The target to collect public records data for
            
        Returns:
            Dictionary containing public records collection results
        """
        self.logger.info(f"Collecting public records data for target: {target}")
        
        try:
            # Use real public records service to find public records
            from ....services.real_public_records_service import perform_public_records_search
            
            # Search for court records related to the target
            court_result = await perform_public_records_search(
                record_type="court_records",
                query=target,
                max_results=10
            )
            
            if "error" not in court_result:
                court_records = court_result.get("records", [])
            else:
                court_records = []
            
            # Also use search scraper tool for additional public records
            tool_results = await self.use_search_tool(target, 10)
            
            collection_data = {
                "source": "public_records_search",
                "target": target,
                "timestamp": time.time(),
                "court_records": court_records,
                "tool_results": tool_results,
                "total_results": len(court_records) + tool_results.get("count", 0),
                "collection_success": True,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Public records data collected for {target}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error collecting public records data for {target}: {str(e)}")
            return {
                "error": str(e),
                "source": "public_records_search",
                "target": target,
                "collection_success": False
            }

# Add alias for backward compatibility
PublicRecordsCollector = PublicRecordsCollectorAgent