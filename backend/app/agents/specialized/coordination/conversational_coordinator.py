"""
Conversational Coordinator Agent

This agent manages conversation flow, intent analysis, and context coordination
between specialized agents. Migrated from unified_agent.py with enhanced
capabilities.
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from enum import Enum

from pydantic import BaseModel, Field

from ...base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class ConversationState(BaseModel):
    """State for a conversation thread."""
    pipeline_id: str
    user_id: Optional[str] = None
    urls: List[str] = Field(default_factory=list)
    schema: Dict[str, Any] = Field(default_factory=dict)
    generated_code: str = ""
    current_phase: str = "initial"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Intent(BaseModel):
    """Analyzed user intent."""
    primary_intent: str = Field(description="Primary user intent")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions: List[str] = Field(default_factory=list)
    similar_pipelines: List[str] = Field(default_factory=list)


class ConversationalCoordinatorAgent(LLMOSINTAgent):
    """
    Agent responsible for coordinating conversation flow and intent analysis.
    
    This agent manages the conversational interface, analyzes user intent,
    maintains context, and coordinates between other specialized agents.
    Migrated functionality from unified_agent.py and openrouter_agent.py.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="Conversational Coordinator",
                description="Manages conversation flow and coordinates specialized agents",
                max_iterations=5,
                timeout=180,
                temperature=0.3
            )
        
        super().__init__(config=config, **kwargs)
        
        # Conversation management
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.conversation_contexts: Dict[str, ConversationState] = {}
        self.conversation_ttl = 86400 * 7  # 7 days
        
        # Intent patterns
        self.intent_patterns = {
            "add_urls": ["add url", "search for", "find url", "scrape", "extract from"],
            "define_schema": ["schema", "field", "extract", "data structure", "define"],
            "generate_code": ["generate code", "create code", "python code", "write code"],
            "run_pipeline": ["run", "execute", "start", "process", "scrape now"],
            "ask_question": ["help", "how to", "what is", "explain", "question"],
            "reuse_pipeline": ["similar", "template", "reuse", "existing", "previous"],
            "optimize_pipeline": ["optimize", "improve", "better", "faster", "enhance"]
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for conversation coordination."""
        required_fields = ["message", "pipeline_id"]
        
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        message = input_data.get("message", "").strip()
        if not message:
            self.logger.error("Empty message provided")
            return False
        
        pipeline_id = input_data.get("pipeline_id", "").strip()
        if not pipeline_id:
            self.logger.error("Empty pipeline_id provided")
            return False
        
        return True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for conversation coordination."""
        return """You are a Conversational Coordinator for ScrapeCraft, an intelligent web scraping platform.

Your role is to:
1. Analyze user intent and understand their scraping needs
2. Maintain conversation context and flow
3. Coordinate between specialized agents (URL discovery, schema definition, code generation)
4. Provide helpful, conversational guidance throughout the process
5. Suggest next steps and optimizations

Key capabilities:
- Natural conversation understanding
- Intent recognition and analysis
- Context management across sessions
- Intelligent suggestion of next actions
- Pipeline coordination and workflow management

Always analyze the user's message and determine:
1. What they want to do (primary intent)
2. What information/entities they provided
3. What the next logical step should be
4. How to guide them toward their goal

Structure your response as valid JSON:
{
    "primary_intent": "add_urls|define_schema|generate_code|run_pipeline|ask_question|reuse_pipeline|optimize_pipeline",
    "confidence": 0.0-1.0,
    "entities": {
        "urls": ["list of URLs if provided"],
        "search_query": "search query if they want to find URLs",
        "fields": {"field_name": "field_type"},
        "description": "what they want to scrape"
    },
    "suggested_actions": ["list of next actions to suggest"],
    "response_message": "natural conversational response to the user",
    "context_updates": {
        "urls_to_add": ["urls to add to context"],
        "schema_updates": {"fields": "to add"},
        "phase": "new phase if applicable"
    }
}

Be conversational, helpful, and proactive in guiding users toward successful scraping pipelines."""
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process the raw output from intent analysis."""
        try:
            # Check if this is a fallback response
            if "[This response was generated using local analysis" in raw_output:
                return self._generate_fallback_response()
            
            # Clean and parse JSON output
            cleaned_output = self._clean_json_output(raw_output)
            
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    structured_data = self._parse_text_response(cleaned_output)
            
            # Validate and enhance the response
            return self._validate_and_enhance_response(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing conversational output: {e}")
            return self._generate_fallback_response()
    
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
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text response into structured data."""
        # Simple fallback parser
        return {
            "primary_intent": "ask_question",
            "confidence": 0.5,
            "entities": {},
            "suggested_actions": ["clarify_request"],
            "response_message": text[:500],  # Truncate if too long
            "context_updates": {}
        }
    
    def _validate_and_enhance_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the conversational response."""
        enhanced = response.copy()
        
        # Ensure required fields exist
        required_fields = [
            "primary_intent", "confidence", "entities", 
            "suggested_actions", "response_message", "context_updates"
        ]
        
        for field in required_fields:
            if field not in enhanced:
                if field == "primary_intent":
                    enhanced[field] = "ask_question"
                elif field == "confidence":
                    enhanced[field] = 0.5
                elif field in ["entities", "suggested_actions", "context_updates"]:
                    enhanced[field] = {}
                elif field == "response_message":
                    enhanced[field] = "I'm here to help with your scraping needs."
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "intent_confidence": enhanced["confidence"]
        }
        
        return enhanced
    
    def _generate_fallback_response(self) -> Dict[str, Any]:
        """Generate fallback response when processing fails."""
        return {
            "primary_intent": "ask_question",
            "confidence": 0.3,
            "entities": {},
            "suggested_actions": [
                "add_urls",
                "define_schema", 
                "generate_code",
                "run_pipeline"
            ],
            "response_message": "I can help you build web scraping pipelines! You can:\n"
                              "- Add URLs to scrape\n"
                              "- Define data schema\n"
                              "- Generate Python code\n"
                              "- Run the pipeline\n\n"
                              "What would you like to do?",
            "context_updates": {},
            "metadata": {
                "agent_id": self.config.agent_id,
                "fallback": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _get_required_output_fields(self) -> List[str]:
        """Get required output fields for this agent."""
        return [
            "primary_intent",
            "confidence", 
            "entities",
            "suggested_actions",
            "response_message"
        ]
    
    async def analyze_intent(
        self, 
        message: str, 
        pipeline_id: str,
        context: Optional[ConversationState] = None
    ) -> Intent:
        """
        Analyze user intent with conversation context.
        
        Args:
            message: User's message
            pipeline_id: Pipeline identifier
            context: Optional conversation context
            
        Returns:
            Analyzed intent with confidence and suggestions
        """
        # Get conversation history for context
        history = self._get_conversation_history(pipeline_id, limit=5)
        
        # Build context for intent analysis
        history_text = "\n".join([
            f"{msg['role']}: {msg['content'][:200]}"
            for msg in reversed(history)
        ])
        
        # Prepare input for intent analysis
        input_data = {
            "message": message,
            "pipeline_id": pipeline_id,
            "history": history_text,
            "current_context": context.model_dump() if context else {},
            "request_type": "intent_analysis"
        }
        
        # Execute intent analysis
        result = await self.execute(input_data)
        
        if result.success:
            response_data = result.data
            return Intent(
                primary_intent=response_data.get("primary_intent", "ask_question"),
                confidence=response_data.get("confidence", 0.5),
                entities=response_data.get("entities", {}),
                suggested_actions=response_data.get("suggested_actions", []),
                similar_pipelines=response_data.get("similar_pipelines", [])
            )
        else:
            # Fallback intent
            return Intent(
                primary_intent="ask_question",
                confidence=0.3,
                entities={},
                suggested_actions=["clarify_request"],
                similar_pipelines=[]
            )
    
    def _get_conversation_history(self, pipeline_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a pipeline."""
        return self.conversation_history.get(pipeline_id, [])[-limit:]
    
    def _add_to_conversation(self, pipeline_id: str, role: str, content: str):
        """Add a message to conversation history."""
        if pipeline_id not in self.conversation_history:
            self.conversation_history[pipeline_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.conversation_history[pipeline_id].append(message)
        
        # Keep only last 50 messages
        if len(self.conversation_history[pipeline_id]) > 50:
            self.conversation_history[pipeline_id] = self.conversation_history[pipeline_id][-50:]
    
    def get_or_create_context(
        self, 
        pipeline_id: str, 
        user_id: Optional[str] = None,
        initial_context: Optional[Dict] = None
    ) -> ConversationState:
        """Get existing context or create new one."""
        if pipeline_id in self.conversation_contexts:
            context = self.conversation_contexts[pipeline_id]
            
            # Update with any new context data
            if initial_context:
                if initial_context.get('urls'):
                    context.urls = list(set(context.urls + initial_context['urls']))
                if initial_context.get('schema'):
                    context.schema.update(initial_context['schema'])
                if initial_context.get('generated_code'):
                    context.generated_code = initial_context['generated_code']
                if initial_context.get('current_phase'):
                    context.current_phase = initial_context['current_phase']
            
            context.last_updated = datetime.utcnow()
            return context
        
        # Create new context
        context = ConversationState(
            pipeline_id=pipeline_id,
            user_id=user_id,
            urls=initial_context.get('urls', []) if initial_context else [],
            schema=initial_context.get('schema', {}) if initial_context else {},
            generated_code=initial_context.get('generated_code', '') if initial_context else '',
            current_phase=initial_context.get('current_phase', 'initial') if initial_context else 'initial',
            metadata=initial_context.get('metadata', {}) if initial_context else {}
        )
        
        self.conversation_contexts[pipeline_id] = context
        return context
    
    def update_context(self, pipeline_id: str, context_updates: Dict[str, Any]):
        """Update conversation context."""
        if pipeline_id not in self.conversation_contexts:
            return
        
        context = self.conversation_contexts[pipeline_id]
        
        if 'urls_to_add' in context_updates:
            new_urls = [url for url in context_updates['urls_to_add'] if url not in context.urls]
            context.urls.extend(new_urls)
        
        if 'schema_updates' in context_updates:
            context.schema.update(context_updates['schema_updates'])
        
        if 'generated_code' in context_updates:
            context.generated_code = context_updates['generated_code']
        
        if 'phase' in context_updates:
            context.current_phase = context_updates['phase']
        
        if 'metadata' in context_updates:
            context.metadata.update(context_updates['metadata'])
        
        context.last_updated = datetime.utcnow()
    
    def clear_conversation(self, pipeline_id: str):
        """Clear conversation data for a pipeline."""
        if pipeline_id in self.conversation_history:
            del self.conversation_history[pipeline_id]
        
        if pipeline_id in self.conversation_contexts:
            del self.conversation_contexts[pipeline_id]
    
    def get_conversation_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get status of conversation for a pipeline."""
        history = self._get_conversation_history(pipeline_id)
        context = self.conversation_contexts.get(pipeline_id)
        
        return {
            "pipeline_id": pipeline_id,
            "message_count": len(history),
            "last_message": history[-1] if history else None,
            "context": context.model_dump() if context else None,
            "current_phase": context.current_phase if context else "none",
            "urls_count": len(context.urls) if context else 0,
            "schema_fields": len(context.schema) if context else 0,
            "has_code": bool(context.generated_code) if context else False
        }