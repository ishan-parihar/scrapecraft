"""
LLM Integration Service for OSINT Operations

This service provides a unified interface for different LLM providers
to support high-level OSINT operations through agentic LLM capabilities.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(BaseModel):
    """LLM provider configuration and client."""
    name: str
    base_url: str
    api_key: str
    model: str
    provider_type: str  # "openai-compatible", "openrouter", "openai"
    headers: Dict[str, str] = {}
    timeout: int = 120
    max_retries: int = 3

class LLMIntegrationService:
    """
    Unified LLM integration service supporting multiple providers.
    """
    
    def __init__(self):
        self.provider = self._initialize_provider()
        self.logger = logging.getLogger(f"{__name__}.LLMIntegrationService")
        
        # HTTP client configuration
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),  # Increased timeout for complex analysis
            headers=self.provider.headers
        )
        
        self.logger.info(f"LLM Integration initialized with provider: {self.provider.name}")
    
    def _initialize_provider(self) -> LLMProvider:
        """Initialize the LLM provider based on configuration."""
        
        if settings.LLM_PROVIDER == "custom" and settings.CUSTOM_LLM_ENABLED:
            return LLMProvider(
                name="Custom LLM",
                base_url=settings.CUSTOM_LLM_BASE_URL,
                api_key=settings.CUSTOM_LLM_API_KEY,
                model=settings.CUSTOM_LLM_MODEL,
                provider_type=settings.CUSTOM_LLM_PROVIDER_TYPE,
                headers={
                    "Authorization": f"Bearer {settings.CUSTOM_LLM_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        elif settings.LLM_PROVIDER == "openrouter" and settings.OPENROUTER_API_KEY:
            return LLMProvider(
                name="OpenRouter",
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                model=settings.OPENROUTER_MODEL,
                provider_type="openrouter",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://scrapecraft.osint",
                    "X-Title": "ScrapeCraft OSINT"
                }
            )
        
        elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return LLMProvider(
                name="OpenAI",
                base_url=settings.OPENAI_BASE_URL,
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                provider_type="openai",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        else:
            # No valid LLM provider configured - raise error instead of using mock
            raise ValueError(
                "No valid LLM provider configured. Please configure OPENROUTER_API_KEY, "
                "OPENAI_API_KEY, or enable CUSTOM_LLM. Mock services have been disabled "
                "to ensure real OSINT functionality."
            )
    
    async def generate_intelligence_insights(
        self, 
        context: Dict[str, Any],
        investigation_query: str
    ) -> Dict[str, Any]:
        """
        Generate intelligence insights using LLM based on collected data.
        
        Args:
            context: Dictionary containing collected OSINT data
            investigation_query: Original investigation query
            
        Returns:
            Dictionary with intelligence insights and analysis
        """
        
        try:
            # Prepare context for LLM
            context_summary = self._prepare_context_summary(context)
            
            system_prompt = """You are an expert OSINT (Open Source Intelligence) analyst. 
            Your task is to analyze the provided intelligence data and generate actionable insights.
            
            Focus on:
            1. Key entities and their relationships
            2. Patterns and trends
            3. Risk factors and threats
            4. Strategic implications
            5. Actionable recommendations
            
            Provide structured, analytical output that supports decision-making."""
            
            user_prompt = f"""
            Investigation: {investigation_query}
            
            Data: {context_summary}
            
            Provide brief analysis:
            
            EXECUTIVE SUMMARY: [2 sentences]
            
            KEY FINDINGS:
            - [Finding 1]
            - [Finding 2]
            
            RISKS: [Main risks]
            
            RECOMMENDATIONS:
            - [Action 1]
            - [Action 2]
            
            Keep it concise.
            """
            
            response = await self._call_llm(system_prompt, user_prompt)
            
            # Parse and structure the response
            try:
                # Try to parse as JSON first (for backward compatibility)
                try:
                    insights = json.loads(response)
                    if isinstance(insights, dict):
                        parsed_insights = insights
                    else:
                        parsed_insights = {"analysis": str(insights)}
                except json.JSONDecodeError:
                    # Parse structured text response
                    parsed_insights = self._parse_structured_response(response)
                
                # Check if this is a timeout/error response
                if parsed_insights.get("timeout") or parsed_insights.get("api_error"):
                    self.logger.warning(f"LLM returned fallback response: {parsed_insights.get('error', 'Unknown error')}")
                    return {
                        "insights": {
                            "executive_summary": f"Limited analysis due to API issues: {parsed_insights.get('error', 'Unknown error')}",
                            "key_findings": ["Analysis limited due to API timeout/error"],
                            "entity_analysis": {"persons": [], "organizations": [], "locations": []},
                            "pattern_recognition": {"observed_patterns": [], "confidence": "Low"},
                            "risk_assessment": {"overall_risk": "Unknown", "factors": ["API limitations"]},
                            "strategic_insights": ["Retry analysis when API is available"],
                            "recommendations": ["Consider manual analysis", "Check API configuration"]
                        },
                        "confidence": 0.2,  # Low confidence for fallback responses
                        "source": "llm_fallback",
                        "generated_at": datetime.utcnow().isoformat(),
                        "provider": self.provider.name,
                        "error": parsed_insights.get("error", "API timeout/error")
                    }
                
                return {
                    "insights": parsed_insights,
                    "confidence": 0.85,
                    "source": "llm_analysis",
                    "generated_at": datetime.utcnow().isoformat(),
                    "provider": self.provider.name
                }
            except Exception as parse_error:
                # Fallback if parsing fails
                self.logger.warning(f"Response parsing failed: {parse_error}")
                return {
                    "insights": {
                        "executive_summary": response[:500] if len(response) > 500 else response,
                        "analysis": response,
                        "format_note": "Raw text response due to parsing limitation"
                    },
                    "confidence": 0.6,
                    "source": "llm_analysis",
                    "generated_at": datetime.utcnow().isoformat(),
                    "provider": self.provider.name
                }
                
        except Exception as e:
            self.logger.error(f"LLM intelligence generation failed: {e}")
            return {
                "error": f"Intelligence analysis unavailable: {e}",
                "service_unavailable": True
            }
    
    async def enhance_search_query(
        self, 
        original_query: str,
        search_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance search queries using LLM to improve OSINT collection.
        
        Args:
            original_query: Original search query
            search_context: Optional context about the investigation
            
        Returns:
            Dictionary with enhanced queries and search strategy
        """
        
        try:
            system_prompt = """You are an expert OSINT researcher. 
            Your task is to enhance search queries to maximize information discovery.
            Generate variations, synonyms, and context-specific terms."""
            
            user_prompt = f"""
            Original Query: {original_query}
            Context: {search_context or 'General OSINT investigation'}
            
            Please provide:
            1. Enhanced primary query (more specific)
            2. Alternative queries (3 variations)
            3. Key search terms (important keywords)
            4. Exclusion terms (terms to exclude)
            5. Search strategy recommendations
            
            Format as JSON.
            """
            
            response = await self._call_llm(system_prompt, user_prompt)
            
            try:
                enhanced = json.loads(response)
                return {
                    "enhanced_queries": enhanced,
                    "original_query": original_query,
                    "provider": self.provider.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    "error": f"Search enhancement unavailable: {e}",
                    "service_unavailable": True
                }
                
        except Exception as e:
            self.logger.error(f"Query enhancement failed: {e}")
            return {
                "error": f"Search enhancement unavailable: {e}",
                "service_unavailable": True
            }
    
    async def analyze_data_for_patterns(
        self, 
        data: Dict[str, Any],
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Analyze collected data for patterns using LLM.
        
        Args:
            data: Collected OSINT data
            analysis_type: Type of pattern analysis (temporal, network, behavioral, etc.)
            
        Returns:
            Dictionary with pattern analysis results
        """
        
        try:
            data_summary = json.dumps(data, indent=2, default=str)[:2000]  # Limit size
            
            system_prompt = f"""You are an expert pattern recognition analyst for OSINT investigations.
            Analyze the provided data for {analysis_type} patterns."""
            
            user_prompt = f"""
            Analysis Type: {analysis_type}
            
            Data to Analyze:
            {data_summary}
            
            Please identify:
            1. Key patterns observed
            2. Anomalies or outliers
            3. Connections and relationships
            4. Temporal sequences (if applicable)
            5. Significance assessment
            
            Format as structured JSON analysis.
            """
            
            response = await self._call_llm(system_prompt, user_prompt)
            
            try:
                patterns = json.loads(response)
                return {
                    "pattern_analysis": patterns,
                    "analysis_type": analysis_type,
                    "confidence": 0.8,
                    "provider": self.provider.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    "error": "Pattern analysis failed - invalid response format",
                    "service_unavailable": True
                }
                
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            return {
                "error": f"Pattern analysis unavailable: {e}",
                "service_unavailable": True
            }
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to LLM provider with timeout and error handling."""
        
        payload = {
            "model": self.provider.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000  # Further reduced for faster response
        }
        
        for attempt in range(self.provider.max_retries):
            try:
                # Use a shorter timeout for each attempt
                response = await asyncio.wait_for(
                    self.http_client.post(
                        f"{self.provider.base_url}/chat/completions",
                        json=payload
                    ),
                    timeout=30.0  # 30 second timeout per attempt for complex analysis
                )
                
                response.raise_for_status()
                
                result = response.json()
                
                # Handle different response formats
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                elif "data" in result:
                    # Some APIs return data in a different format
                    if isinstance(result["data"], list) and len(result["data"]) > 0:
                        return result["data"][0].get("content", str(result["data"][0]))
                    else:
                        return str(result["data"])
                elif "content" in result:
                    return result["content"]
                elif "response" in result:
                    return result["response"]
                else:
                    # Return the raw response as fallback
                    self.logger.warning(f"Unexpected API response format: {list(result.keys())}")
                    return str(result)
                
            except asyncio.TimeoutError:
                self.logger.warning(f"LLM request timeout on attempt {attempt + 1}")
                if attempt == self.provider.max_retries - 1:
                    # Return fallback response on timeout
                    return json.dumps({
                        "error": "LLM request timeout",
                        "fallback_response": "Analysis limited due to API timeout",
                        "timeout": True
                    })
                await asyncio.sleep(1)  # Short delay before retry
                
            except Exception as e:
                self.logger.error(f"LLM request error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.provider.max_retries - 1:
                    # Return fallback response on error
                    return json.dumps({
                        "error": str(e),
                        "fallback_response": "Analysis limited due to API error",
                        "api_error": True
                    })
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured text response into dictionary format."""
        
        insights = {}
        lines = response.strip().split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if line.endswith(':') and not line.startswith('-'):
                # Save previous section if exists
                if current_section and section_content:
                    insights[current_section.lower().replace(' ', '_')] = '\n'.join(section_content).strip()
                
                # Start new section
                current_section = line[:-1].upper()
                section_content = []
                
            elif line.startswith('- ') or line.startswith('• '):
                # Bullet points
                section_content.append(line[2:])
            elif line and current_section:
                # Regular content
                section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            insights[current_section.lower().replace(' ', '_')] = '\n'.join(section_content).strip()
        
        # Ensure we have at least some content
        if not insights:
            insights = {"analysis": response}
        
        return insights
    
    def _prepare_context_summary(self, context: Dict[str, Any]) -> str:
        """Prepare a concise summary of OSINT context for LLM analysis."""
        
        summary_parts = []
        
        # Surface web results
        surface_data = context.get("surface_web", {})
        if surface_data.get("articles"):
            summary_parts.append(f"Surface Web: Found {len(surface_data['articles'])} articles")
            for article in surface_data["articles"][:3]:
                summary_parts.append(f"- {article.get('title', 'No title')}")
        
        # Social media results
        social_data = context.get("social_media", {})
        if social_data.get("posts"):
            summary_parts.append(f"Social Media: Found {len(social_data['posts'])} posts")
            for post in social_data["posts"][:2]:
                summary_parts.append(f"- {post.get('content', 'No content')[:100]}...")
        
        # Public records
        records_data = context.get("public_records", {})
        if records_data.get("records"):
            summary_parts.append(f"Public Records: Found {len(records_data['records'])} records")
        
        # Collection metadata
        metadata = context.get("metadata", {})
        if metadata:
            summary_parts.append(f"Collection used {len(metadata.get('sources_used', []))} sources")
        
        return "\n".join(summary_parts) if summary_parts else "No data collected"
    
    async def validate_connection(self) -> bool:
        """Validate LLM provider connection."""
        
        try:
            payload = {
                "model": self.provider.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            response = await self.http_client.post(
                f"{self.provider.base_url}/chat/completions",
                json=payload
            )
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"LLM connection validation failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

# Global LLM service instance
_llm_service = None

# LLM integration availability flag
LLM_AVAILABLE = True

async def get_llm_service() -> LLMIntegrationService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMIntegrationService()
    return _llm_service

async def close_llm_service():
    """Close the global LLM service."""
    global _llm_service
    if _llm_service:
        await _llm_service.close()
        _llm_service = None