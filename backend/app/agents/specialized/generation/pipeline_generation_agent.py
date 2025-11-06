"""
Pipeline Generation Agent

This agent generates optimized scraping pipelines and Python code.
Consolidates code generation functionality from multiple legacy agents.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from pydantic import BaseModel

from ...base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class GeneratedPipeline(BaseModel):
    """Generated scraping pipeline with metadata."""
    pipeline_id: str
    name: str
    description: str
    code: str
    urls: List[str]
    schema: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    confidence: float = 0.8
    optimizations: List[str] = []


class PipelineGenerationAgent(LLMOSINTAgent):
    """
    Agent responsible for generating optimized scraping pipelines.
    
    This agent creates production-ready Python code for web scraping
    using ScrapeGraphAI and other tools. Consolidates functionality
    from openrouter_agent.py, simple_agent.py, and unified_agent.py.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="Pipeline Generation Specialist",
                description="Generates optimized scraping pipelines and Python code",
                max_iterations=3,
                timeout=150,
                temperature=0.1
            )
        
        super().__init__(config=config, **kwargs)
        
        # Code templates and patterns
        self.code_templates = {
            "basic_scraper": "async_basic",
            "advanced_scraper": "async_with_retry", 
            "batch_scraper": "async_concurrent",
            "scheduled_scraper": "async_with_scheduling"
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            "concurrency": "Add concurrent execution",
            "retry_logic": "Implement retry mechanisms",
            "error_handling": "Add comprehensive error handling",
            "rate_limiting": "Add rate limiting",
            "caching": "Implement result caching",
            "monitoring": "Add progress monitoring"
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for pipeline generation."""
        # Check for required combinations
        has_urls = bool(input_data.get("urls"))
        has_schema = bool(input_data.get("schema"))
        has_description = bool(input_data.get("description"))
        
        # Need at least URLs and schema, or a description to work with
        if not (has_urls and has_schema) and not has_description:
            self.logger.error("Need either URLs+schema or description to generate pipeline")
            return False
        
        # Validate URLs if provided
        if has_urls:
            urls = input_data.get("urls", [])
            if not isinstance(urls, list) or len(urls) == 0:
                self.logger.error("URLs must be a non-empty list")
                return False
        
        # Validate schema if provided
        if has_schema:
            schema = input_data.get("schema", {})
            if not isinstance(schema, dict) or len(schema) == 0:
                self.logger.error("Schema must be a non-empty dictionary")
                return False
        
        return True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for pipeline generation."""
        return """You are a Pipeline Generation Specialist for ScrapeCraft, an intelligent web scraping platform.

Your role is to:
1. Generate production-ready Python scraping code
2. Optimize code for performance and reliability
3. Implement proper error handling and retry logic
4. Use best practices for async programming
5. Create clear, maintainable, and well-documented code

Key requirements:
- Always use async/await patterns for better performance
- Implement proper error handling with try-except blocks
- Add retry logic with exponential backoff
- Use ScrapeGraphAI's AsyncClient for scraping
- Include progress monitoring and logging
- Generate code that is ready to run with minimal configuration

Structure your response as valid JSON:
{
    "pipeline": {
        "name": "descriptive pipeline name",
        "description": "brief description of what this pipeline does",
        "code": "complete, runnable Python code",
        "urls": ["list of URLs this pipeline targets"],
        "schema": {"field": "type", ...},
        "extraction_prompt": "the prompt used for data extraction"
    },
    "optimizations": ["list of optimizations applied"],
    "requirements": ["list of requirements or dependencies"],
    "usage_instructions": "how to run this pipeline",
    "expected_output": "description of expected output format",
    "confidence": 0.0-1.0,
    "recommendations": ["list of recommendations for improvement"]
}

Focus on creating code that is production-ready and well-documented."""
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process the raw output from pipeline generation."""
        try:
            # Check if this is a fallback response
            if "[This response was generated using local analysis" in raw_output:
                return self._generate_fallback_pipeline()
            
            # Clean and parse JSON output
            cleaned_output = self._clean_json_output(raw_output)
            
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: generate basic pipeline
                    structured_data = self._generate_basic_pipeline()
            
            # Validate and enhance the response
            return self._validate_and_enhance_pipeline(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing pipeline generation output: {e}")
            return self._generate_fallback_pipeline()
    
    def _clean_json_output(self, raw_output: str) -> str:
        """Clean raw output to extract valid JSON."""
        cleaned = raw_output.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        # Extract JSON content
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace+1]
        
        return cleaned
    
    def _generate_basic_pipeline(self) -> Dict[str, Any]:
        """Generate a basic pipeline structure."""
        return {
            "pipeline": {
                "name": "Basic Web Scraper",
                "description": "Basic async web scraping pipeline",
                "code": self._get_basic_code_template(),
                "urls": ["https://example.com"],
                "schema": {"title": "str", "content": "str"},
                "extraction_prompt": "Extract title and content from the webpage"
            },
            "optimizations": ["async execution", "basic error handling"],
            "requirements": ["scrapegraph-py", "asyncio"],
            "usage_instructions": "Run with: python pipeline.py",
            "expected_output": "JSON with extracted data",
            "confidence": 0.6,
            "recommendations": ["Add retry logic", "Implement concurrent processing"]
        }
    
    def _get_basic_code_template(self) -> str:
        """Get basic code template."""
        return '''import asyncio
from typing import List, Dict, Any
from scrapegraph_py import AsyncClient
import json

async def scrape_url(client: AsyncClient, url: str, prompt: str) -> Dict:
    \"\"\"Scrape a single URL with basic error handling.\"\"\"
    try:
        result = await client.smartscraper(
            website_url=url,
            user_prompt=prompt
        )
        return {"success": True, "url": url, "data": result}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}

async def main_pipeline(urls: List[str], prompt: str) -> Dict:
    \"\"\"Main scraping pipeline.\"\"\"
    results = []
    
    async with AsyncClient(api_key="your-api-key") as client:
        for url in urls:
            result = await scrape_url(client, url, prompt)
            results.append(result)
    
    return {"results": results}

if __name__ == "__main__":
    urls = ["https://example.com"]
    prompt = "Extract title and content"
    
    results = asyncio.run(main_pipeline(urls, prompt))
    print(json.dumps(results, indent=2))'''
    
    def _validate_and_enhance_pipeline(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the pipeline generation response."""
        enhanced = response.copy()
        
        # Ensure required fields exist
        if "pipeline" not in enhanced:
            enhanced["pipeline"] = {}
        
        pipeline = enhanced["pipeline"]
        
        # Ensure pipeline has required fields
        if "code" not in pipeline:
            pipeline["code"] = self._get_basic_code_template()
        
        if "optimizations" not in enhanced:
            enhanced["optimizations"] = ["async execution"]
        
        if "requirements" not in enhanced:
            enhanced["requirements"] = ["scrapegraph-py", "asyncio"]
        
        if "confidence" not in enhanced:
            enhanced["confidence"] = 0.7
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "code_lines": len(pipeline["code"].split('\n')),
            "has_error_handling": "try:" in pipeline["code"],
            "is_async": "async def" in pipeline["code"]
        }
        
        return enhanced
    
    def _generate_fallback_pipeline(self) -> Dict[str, Any]:
        """Generate fallback pipeline when processing fails."""
        return {
            "pipeline": {
                "name": "Fallback Scraper",
                "description": "Basic scraper generated as fallback",
                "code": self._get_basic_code_template(),
                "urls": ["https://example.com"],
                "schema": {"title": "str"},
                "extraction_prompt": "Extract basic information"
            },
            "optimizations": ["basic structure"],
            "requirements": ["scrapegraph-py"],
            "usage_instructions": "Configure API key and run",
            "expected_output": "Basic extracted data",
            "confidence": 0.3,
            "recommendations": ["Enhance error handling", "Add monitoring"],
            "metadata": {
                "agent_id": self.config.agent_id,
                "fallback": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _get_required_output_fields(self) -> List[str]:
        """Get required output fields for this agent."""
        return [
            "pipeline",
            "optimizations",
            "requirements",
            "usage_instructions"
        ]
    
    async def generate_pipeline(
        self,
        urls: List[str],
        schema: Dict[str, Any],
        description: str = "",
        optimizations: Optional[List[str]] = None
    ) -> GeneratedPipeline:
        """Generate a complete scraping pipeline."""
        # Create extraction prompt from schema
        field_descriptions = []
        for field_name, field_type in schema.items():
            field_desc = field_name.replace('_', ' ').lower()
            field_descriptions.append(f"- {field_name}: {field_desc}")
        
        extraction_prompt = f"""Extract the following information from the webpage:
{"\\n".join(field_descriptions)}

Return the data as JSON with these exact field names."""
        
        # Prepare input for pipeline generation
        input_data = {
            "urls": urls,
            "schema": schema,
            "description": description or f"Extract {', '.join(schema.keys())}",
            "extraction_prompt": extraction_prompt,
            "optimizations": optimizations or ["concurrency", "retry_logic", "error_handling"],
            "request_type": "pipeline_generation"
        }
        
        # Execute pipeline generation
        result = await self.execute(input_data)
        
        if result.success:
            response_data = result.data
            pipeline_data = response_data.get("pipeline", {})
            
            generated_pipeline = GeneratedPipeline(
                pipeline_id=f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                name=pipeline_data.get("name", "Generated Pipeline"),
                description=pipeline_data.get("description", ""),
                code=pipeline_data.get("code", ""),
                urls=pipeline_data.get("urls", urls),
                schema=pipeline_data.get("schema", schema),
                metadata={
                    "extraction_prompt": extraction_prompt,
                    "optimizations": response_data.get("optimizations", []),
                    "requirements": response_data.get("requirements", []),
                    "usage_instructions": response_data.get("usage_instructions", ""),
                    "expected_output": response_data.get("expected_output", ""),
                    "performance_notes": response_data.get("performance_notes", ""),
                    "generated_by": self.config.agent_id
                },
                confidence=response_data.get("confidence", 0.7),
                optimizations=response_data.get("optimizations", [])
            )
            
            return generated_pipeline
        else:
            self.logger.error(f"Pipeline generation failed: {result.error_message}")
            # Return fallback pipeline
            return GeneratedPipeline(
                pipeline_id=f"fallback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                name="Fallback Pipeline",
                description="Basic pipeline due to generation failure",
                code=self._get_basic_code_template(),
                urls=urls,
                schema=schema,
                metadata={"error": result.error_message},
                confidence=0.3,
                optimizations=["basic"]
            )