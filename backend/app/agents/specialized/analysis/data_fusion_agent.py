"""
Data Fusion Agent for OSINT investigations.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json
import re
import hashlib

from ...base.osint_agent import OSINTAgent, LLMOSINTAgent, AgentConfig, AgentResult


class DataFusionAgent(LLMOSINTAgent):
    """
    Agent responsible for fusing and integrating data from multiple sources.
    Handles data deduplication, normalization, correlation, and enrichment.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        # Initialize with default config if not provided
        if not config:
            config = AgentConfig(
                agent_id="data_fusion_agent",
                role="Data Fusion Agent",
                description="Agent responsible for fusing and integrating data from multiple sources. Handles data deduplication, normalization, correlation, and enrichment."
            )
        
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)
        
        # Initialize specific attributes after parent initialization
        self.supported_data_types = [
            "profiles", "contacts", "organizations", "locations",
            "relationships", "activities", "documents", "media"
        ]
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """
        You are a Data Fusion Agent, a specialized AI assistant for OSINT investigations.
        Your role is to fuse and integrate data from multiple sources, handling data deduplication,
        normalization, correlation, and enrichment. Follow the user's instructions carefully
        and provide accurate, structured data fusion results while maintaining ethical standards.
        """
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the raw output from the agent into structured data.
        """
        try:
            # Clean the raw output - remove markdown formatting, extra whitespace, etc.
            cleaned_output = self._clean_raw_output(raw_output)
            
            # Try to parse JSON output
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text if embedded
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: parse text manually
                    structured_data = self._parse_text_output(cleaned_output)
            
            # Validate and enhance the structured data
            return self._validate_and_enhance_data(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing output: {e}")
            try:
                cleaned_output = self._clean_raw_output(raw_output)
            except:
                cleaned_output = raw_output  # fallback if cleaning fails
            return {
                "error": "Failed to process output",
                "raw_output": raw_output,
                "cleaned_output": cleaned_output,
                "fallback_data": self._generate_fallback_data()
            }

    def _clean_raw_output(self, raw_output: str) -> str:
        """Clean raw output to extract valid JSON."""
        cleaned = raw_output.strip()
        
        # Remove markdown code block formatting
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]   # Remove ```
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]  # Remove trailing ```
        
        # Remove any leading/trailing text that might be around the JSON
        # Find the first { and last }
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace+1]
        
        return cleaned

    def _validate_and_enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the data fusion results."""
        enhanced = data.copy()
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "confidence_score": self._calculate_fusion_confidence(enhanced),
            "data_quality": self._assess_data_quality(enhanced)
        }
        
        return enhanced

    def _parse_text_output(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text output into structured data."""
        # This is a fallback parser for when JSON parsing fails
        data = {
            "fused_entities": [],
            "fusion_statistics": {},
            "processing_success": True,
            "source": "data_fusion",
            "timestamp": datetime.utcnow().timestamp()
        }
        
        # Simple text parsing logic
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Add basic parsing logic here
            if "fusion" in line.lower() or "entities" in line.lower():
                data["fused_entities"].append({"description": line, "confidence": 0.5})
        
        return data

    def _generate_fallback_data(self) -> Dict[str, Any]:
        """Generate basic data when parsing fails."""
        return {
            "fused_entities": [],
            "fusion_statistics": {},
            "processing_success": True,
            "source": "data_fusion",
            "timestamp": datetime.utcnow().timestamp(),
            "error": "Generated fallback data due to processing error"
        }

    def _calculate_fusion_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for the data fusion results."""
        score = 0.0
        total_checks = 0
        
        # Check for fused entities
        if data.get("fused_entities"):
            score += min(len(data["fused_entities"]) / 10, 1.0)  # Up to 1.0 for 10+ entities
        total_checks += 1
        
        # Check for statistics
        if data.get("fusion_statistics"):
            score += 0.5  # Half point for having statistics
        total_checks += 1
        
        # Check for processing success
        if data.get("processing_success"):
            score += 0.5  # Half point for successful processing
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0

    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data quality metrics."""
        quality_metrics = {
            "completeness": 0.0,
            "consistency": 0.0,
            "accuracy": 0.0,
            "relevance": 0.0
        }
        
        # Basic assessment based on data content
        if data.get("fused_entities"):
            quality_metrics["completeness"] = min(len(data["fused_entities"]) * 0.1, 1.0)
        
        return quality_metrics
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution."""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)

    async def fuse_collection_data(
        self, 
        collection_results: List[Dict[str, Any]],
        fusion_strategy: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Fuse data from multiple collection sources.
        
        Args:
            collection_results: Results from collection agents
            fusion_strategy: Strategy for fusion ("comprehensive", "conservative", "aggressive")
            
        Returns:
            Dictionary containing fused data
        """
        self.logger.info(f"Fusing data from {len(collection_results)} sources using {fusion_strategy} strategy")
        
        try:
            # Extract and categorize data
            categorized_data = await self._categorize_collection_data(collection_results)
            
            # Perform deduplication
            deduplicated_data = await self._deduplicate_data(categorized_data)
            
            # Normalize data formats
            normalized_data = await self._normalize_data(deduplicated_data)
            
            # Correlate related entities
            correlated_data = await self._correlate_entities(normalized_data)
            
            # Enrich with additional context
            enriched_data = await self._enrich_data(correlated_data)
            
            # Calculate confidence scores
            scored_data = await self._calculate_confidence_scores(enriched_data, fusion_strategy)
            
            collection_data = {
                "source": "data_fusion",
                "fusion_strategy": fusion_strategy,
                "timestamp": time.time(),
                "input_sources": len(collection_results),
                "fused_entities": scored_data,
                "fusion_statistics": await self._generate_fusion_stats(collection_results, scored_data),
                "processing_success": True
            }
            
            self.logger.info(f"Data fusion completed, processed {len(scored_data.get('entities', []))} entities")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in data fusion: {str(e)}")
            return {
                "error": str(e),
                "source": "data_fusion",
                "processing_success": False
            }
    
    async def resolve_entity_conflicts(
        self, 
        conflicting_entities: List[Dict[str, Any]],
        resolution_strategy: str = "highest_confidence"
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between different entity versions.
        
        Args:
            conflicting_entities: List of conflicting entity versions
            resolution_strategy: Strategy for conflict resolution
            
        Returns:
            Dictionary containing resolved entity
        """
        self.logger.info(f"Resolving conflicts for {len(conflicting_entities)} entity versions")
        
        try:
            resolved_entity = await self._apply_conflict_resolution(conflicting_entities, resolution_strategy)
            
            resolution_data = {
                "source": "entity_conflict_resolution",
                "resolution_strategy": resolution_strategy,
                "timestamp": time.time(),
                "conflicting_versions": len(conflicting_entities),
                "resolved_entity": resolved_entity,
                "resolution_details": {
                    "fields_resolved": len(resolved_entity.get("resolved_fields", [])),
                    "confidence_improvement": resolved_entity.get("confidence_change", 0),
                    "sources_retained": resolved_entity.get("source_count", 0)
                },
                "resolution_success": True
            }
            
            self.logger.info(f"Entity conflict resolution completed")
            return resolution_data
            
        except Exception as e:
            self.logger.error(f"Error in entity conflict resolution: {str(e)}")
            return {
                "error": str(e),
                "source": "entity_conflict_resolution",
                "resolution_success": False
            }
    
    async def build_relationship_graph(
        self, 
        entities: List[Dict[str, Any]],
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build a relationship graph from fused entities.
        
        Args:
            entities: List of fused entities
            relationship_types: Types of relationships to identify
            
        Returns:
            Dictionary containing relationship graph
        """
        if relationship_types is None:
            relationship_types = ["personal", "professional", "organizational", "temporal", "geographical"]
            
        self.logger.info(f"Building relationship graph for {len(entities)} entities")
        
        try:
            # Identify relationships
            relationships = await self._identify_relationships(entities, relationship_types)
            
            # Build graph structure
            graph_structure = await self._build_graph_structure(entities, relationships)
            
            # Calculate network metrics
            network_metrics = await self._calculate_network_metrics(graph_structure)
            
            # Identify key entities and communities
            analysis_results = await self._analyze_network_structure(graph_structure)
            
            graph_data = {
                "source": "relationship_graph",
                "timestamp": time.time(),
                "entities": len(entities),
                "relationships": len(relationships),
                "relationship_types": relationship_types,
                "graph_structure": graph_structure,
                "network_metrics": network_metrics,
                "analysis_results": analysis_results,
                "construction_success": True
            }
            
            self.logger.info(f"Relationship graph built with {len(relationships)} connections")
            return graph_data
            
        except Exception as e:
            self.logger.error(f"Error building relationship graph: {str(e)}")
            return {
                "error": str(e),
                "source": "relationship_graph",
                "construction_success": False
            }
    
    async def create_temporal_analysis(
        self, 
        entities: List[Dict[str, Any]],
        time_window: str = "30d"
    ) -> Dict[str, Any]:
        """
        Create temporal analysis of entity activities and changes.
        
        Args:
            entities: List of entities with temporal data
            time_window: Time window for analysis
            
        Returns:
            Dictionary containing temporal analysis
        """
        self.logger.info(f"Creating temporal analysis for {len(entities)} entities over {time_window}")
        
        try:
            # Extract timeline data
            timeline_data = await self._extract_timeline_data(entities, time_window)
            
            # Identify patterns and trends
            temporal_patterns = await self._identify_temporal_patterns(timeline_data)
            
            # Detect anomalies
            anomalies = await self._detect_temporal_anomalies(timeline_data)
            
            # Predict future activities
            predictions = await self._predict_temporal_trends(timeline_data, temporal_patterns)
            
            temporal_data = {
                "source": "temporal_analysis",
                "time_window": time_window,
                "timestamp": time.time(),
                "entities_analyzed": len(entities),
                "timeline_data": timeline_data,
                "temporal_patterns": temporal_patterns,
                "anomalies": anomalies,
                "predictions": predictions,
                "analysis_success": True
            }
            
            self.logger.info(f"Temporal analysis completed with {len(temporal_patterns)} patterns identified")
            return temporal_data
            
        except Exception as e:
            self.logger.error(f"Error in temporal analysis: {str(e)}")
            return {
                "error": str(e),
                "source": "temporal_analysis",
                "analysis_success": False
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a data fusion task.
        
        Args:
            task: Task dictionary containing fusion parameters
            
        Returns:
            Dictionary containing fusion results
        """
        task_type = task.get("task_type", "data_fusion")
        results = []
        
        if task_type == "data_fusion":
            # Data fusion
            collection_results = task.get("collection_results", [])
            fusion_strategy = task.get("fusion_strategy", "comprehensive")
            
            if collection_results:
                result = await self.fuse_collection_data(collection_results, fusion_strategy)
                results.append(result)
        
        elif task_type == "conflict_resolution":
            # Entity conflict resolution
            conflicting_entities = task.get("conflicting_entities", [])
            resolution_strategy = task.get("resolution_strategy", "highest_confidence")
            
            if conflicting_entities:
                result = await self.resolve_entity_conflicts(conflicting_entities, resolution_strategy)
                results.append(result)
        
        elif task_type == "relationship_graph":
            # Relationship graph construction
            entities = task.get("entities", [])
            relationship_types = task.get("relationship_types")
            
            if entities:
                result = await self.build_relationship_graph(entities, relationship_types)
                results.append(result)
        
        elif task_type == "temporal_analysis":
            # Temporal analysis
            entities = task.get("entities", [])
            time_window = task.get("time_window", "30d")
            
            if entities:
                result = await self.create_temporal_analysis(entities, time_window)
                results.append(result)
        
        return {
            "agent_id": self.config.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_operations": len(results),
            "status": "completed"
        }
    
    async def _categorize_collection_data(self, collection_results: List[Dict[str, Any]]) -> Dict[str, List]:
        """Categorize collection data by type."""
        categorized = {data_type: [] for data_type in self.supported_data_types}
        
        for result in collection_results:
            if isinstance(result, dict) and "results" in result:
                for item in result["results"]:
                    data_type = self._classify_data_item(item)
                    if data_type in categorized:
                        categorized[data_type].append(item)
        
        return categorized
    
    def _classify_data_item(self, item: Dict[str, Any]) -> str:
        """Classify a data item into a category."""
        if "username" in item or "profile" in item:
            return "profiles"
        elif "email" in item or "phone" in item:
            return "contacts"
        elif "company" in item or "organization" in item:
            return "organizations"
        elif "address" in item or "location" in item:
            return "locations"
        elif "relationships" in item or "connections" in item:
            return "relationships"
        elif "timestamp" in item or "date" in item:
            return "activities"
        elif "document" in item or "file" in item:
            return "documents"
        else:
            return "media"
    
    async def _deduplicate_data(self, categorized_data: Dict[str, List]) -> Dict[str, List]:
        """Remove duplicate data items."""
        deduplicated = {}
        
        for data_type, items in categorized_data.items():
            seen_hashes = set()
            unique_items = []
            
            for item in items:
                item_hash = self._generate_item_hash(item)
                if item_hash not in seen_hashes:
                    seen_hashes.add(item_hash)
                    unique_items.append(item)
            
            deduplicated[data_type] = unique_items
        
        return deduplicated
    
    def _generate_item_hash(self, item: Dict[str, Any]) -> str:
        """Generate hash for data deduplication."""
        # Use key fields for hashing
        key_fields = ["name", "email", "phone", "username", "id", "url"]
        hash_values = []
        
        for field in key_fields:
            if field in item and item[field]:
                hash_values.append(str(item[field]))
        
        item_string = "|".join(sorted(hash_values))
        return hashlib.md5(item_string.encode()).hexdigest()
    
    async def _normalize_data(self, deduplicated_data: Dict[str, List]) -> Dict[str, List]:
        """Normalize data formats across sources."""
        normalized = {}
        
        for data_type, items in deduplicated_data.items():
            normalized_items = []
            
            for item in items:
                normalized_item = await self._normalize_item(item, data_type)
                normalized_items.append(normalized_item)
            
            normalized[data_type] = normalized_items
        
        return normalized
    
    async def _normalize_item(self, item: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Normalize a single data item."""
        normalized = item.copy()
        
        # Standardize field names
        field_mappings = {
            "profiles": {"fullname": "name", "display_name": "name"},
            "contacts": {"email_address": "email", "phone_number": "phone"},
            "organizations": {"company_name": "name", "org_name": "name"}
        }
        
        if data_type in field_mappings:
            for old_field, new_field in field_mappings[data_type].items():
                if old_field in normalized and new_field not in normalized:
                    normalized[new_field] = normalized[old_field]
        
        # Add normalized timestamp
        if "timestamp" not in normalized:
            normalized["timestamp"] = datetime.now().isoformat()
        
        return normalized
    
    async def _correlate_entities(self, normalized_data: Dict[str, List]) -> Dict[str, Any]:
        """Correlate related entities across data types."""
        correlated = {
            "entities": [],
            "correlations": []
        }
        
        # Create entity index
        entity_index = {}
        
        # Process profiles and create base entities
        for profile in normalized_data.get("profiles", []):
            entity_id = self._generate_entity_id(profile)
            entity = {
                "id": entity_id,
                "type": "person",
                "data": {"profile": profile},
                "sources": ["profile"],
                "confidence": 0.8
            }
            entity_index[entity_id] = entity
        
        # Correlate contacts with profiles
        for contact in normalized_data.get("contacts", []):
            matching_entities = self._find_matching_entities(contact, entity_index)
            
            if matching_entities:
                # Add contact info to existing entity
                entity_id = matching_entities[0]
                entity_index[entity_id]["data"]["contact"] = contact
                entity_index[entity_id]["sources"].append("contact")
                entity_index[entity_id]["confidence"] = min(1.0, entity_index[entity_id]["confidence"] + 0.1)
            else:
                # Create new entity from contact
                entity_id = self._generate_entity_id(contact)
                entity = {
                    "id": entity_id,
                    "type": "person",
                    "data": {"contact": contact},
                    "sources": ["contact"],
                    "confidence": 0.6
                }
                entity_index[entity_id] = entity
        
        correlated["entities"] = list(entity_index.values())
        return correlated
    
    def _generate_entity_id(self, data: Dict[str, Any]) -> str:
        """Generate unique entity ID."""
        identifier_fields = ["name", "email", "phone", "username"]
        identifiers = []
        
        for field in identifier_fields:
            if field in data and data[field]:
                identifiers.append(str(data[field]))
        
        if identifiers:
            entity_string = "|".join(sorted(identifiers))
            return hashlib.md5(entity_string.encode()).hexdigest()[:12]
        else:
            return hashlib.md5(str(data).encode()).hexdigest()[:12]
    
    def _find_matching_entities(self, data: Dict[str, Any], entity_index: Dict[str, Dict]) -> List[str]:
        """Find matching entities for data correlation."""
        matches = []
        
        for entity_id, entity in entity_index.items():
            similarity_score = self._calculate_similarity(data, entity["data"])
            
            if similarity_score > 0.7:  # High similarity threshold
                matches.append(entity_id)
        
        return matches
    
    def _calculate_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Calculate similarity score between two data items."""
        # Simple similarity calculation based on common fields
        common_fields = set(data1.keys()) & set(data2.keys())
        if not common_fields:
            return 0.0
        
        matches = 0
        for field in common_fields:
            if data1[field] and data2[field] and str(data1[field]).lower() == str(data2[field]).lower():
                matches += 1
        
        return matches / len(common_fields)
    
    async def _enrich_data(self, correlated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich data with additional context."""
        enriched = correlated_data.copy()
        
        for entity in enriched["entities"]:
            # Add enrichment metadata
            entity["enrichments"] = {
                "data_completeness": self._calculate_completeness(entity["data"]),
                "source_diversity": len(set(entity["sources"])),
                "last_updated": datetime.now().isoformat()
            }
        
        return enriched
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score."""
        total_fields = 0
        populated_fields = 0
        
        for category, category_data in data.items():
            if isinstance(category_data, dict):
                total_fields += len(category_data)
                populated_fields += len([v for v in category_data.values() if v])
        
        return populated_fields / total_fields if total_fields > 0 else 0.0
    
    async def _calculate_confidence_scores(self, enriched_data: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """Calculate confidence scores for entities."""
        scored_data = enriched_data.copy()
        
        for entity in scored_data["entities"]:
            base_confidence = entity.get("confidence", 0.5)
            
            # Apply strategy-specific adjustments
            if strategy == "conservative":
                confidence_multiplier = 0.8
            elif strategy == "aggressive":
                confidence_multiplier = 1.2
            else:  # comprehensive
                confidence_multiplier = 1.0
            
            # Factor in source diversity and completeness
            source_bonus = min(0.2, len(set(entity["sources"])) * 0.05)
            completeness_bonus = entity["enrichments"]["data_completeness"] * 0.2
            
            final_confidence = min(1.0, (base_confidence * confidence_multiplier) + source_bonus + completeness_bonus)
            entity["final_confidence"] = final_confidence
        
        return scored_data
    
    async def _generate_fusion_stats(self, collection_results: List[Dict[str, Any]], fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fusion statistics."""
        return {
            "input_sources": len(collection_results),
            "total_input_items": sum(len(r.get("results", [])) for r in collection_results),
            "entities_created": len(fused_data.get("entities", [])),
            "deduplication_rate": 0.25,  # Simulated
            "average_confidence": sum(e.get("final_confidence", 0.5) for e in fused_data.get("entities", [])) / len(fused_data.get("entities", [])) if fused_data.get("entities") else 0,
            "processing_time": 2.5  # Simulated
        }
    
    async def _apply_conflict_resolution(self, conflicting_entities: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
        """Apply conflict resolution strategy."""
        if strategy == "highest_confidence":
            resolved = max(conflicting_entities, key=lambda x: x.get("confidence", 0))
        elif strategy == "most_recent":
            resolved = max(conflicting_entities, key=lambda x: x.get("timestamp", ""))
        elif strategy == "merge":
            # Merge all sources
            resolved = conflicting_entities[0].copy()
            for entity in conflicting_entities[1:]:
                resolved.update({k: v for k, v in entity.items() if k not in resolved})
            resolved["confidence"] = sum(e.get("confidence", 0) for e in conflicting_entities) / len(conflicting_entities)
        else:
            resolved = conflicting_entities[0]
        
        resolved["resolved_fields"] = list(resolved.keys())
        resolved["source_count"] = len(conflicting_entities)
        return resolved
    
    async def _identify_relationships(self, entities: List[Dict[str, Any]], relationship_types: List[str]) -> List[Dict[str, Any]]:
        """Identify relationships between entities."""
        relationships = []
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                relationship = self._detect_relationship(entity1, entity2, relationship_types)
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    def _detect_relationship(self, entity1: Dict[str, Any], entity2: Dict[str, Any], relationship_types: List[str]) -> Optional[Dict[str, Any]]:
        """Detect relationship between two entities."""
        # Simple relationship detection based on shared attributes
        if entity1.get("type") == "person" and entity2.get("type") == "person":
            # Check for professional relationships
            if "company" in entity1.get("data", {}).get("profile", {}) and "company" in entity2.get("data", {}).get("profile", {}):
                if entity1["data"]["profile"]["company"] == entity2["data"]["profile"]["company"]:
                    return {
                        "source_entity": entity1["id"],
                        "target_entity": entity2["id"],
                        "type": "professional",
                        "confidence": 0.8,
                        "evidence": "shared_employer"
                    }
        
        return None
    
    async def _build_graph_structure(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build graph structure from entities and relationships."""
        return {
            "nodes": [{"id": e["id"], "type": e["type"], "label": e.get("data", {}).get("profile", {}).get("name", e["id"])} for e in entities],
            "edges": [{"source": r["source_entity"], "target": r["target_entity"], "type": r["type"]} for r in relationships],
            "metadata": {
                "node_count": len(entities),
                "edge_count": len(relationships),
                "density": len(relationships) / (len(entities) * (len(entities) - 1)) if len(entities) > 1 else 0
            }
        }
    
    async def _calculate_network_metrics(self, graph_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate network metrics."""
        return {
            "average_degree": 2.5,  # Simulated
            "clustering_coefficient": 0.3,  # Simulated
            "connected_components": 1,  # Simulated
            "network_diameter": 4,  # Simulated
            "central_nodes": ["node_1", "node_3"]  # Simulated
        }
    
    async def _analyze_network_structure(self, graph_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network structure for communities and key entities."""
        return {
            "communities": [
                {"id": 1, "nodes": ["node_1", "node_2", "node_3"], "topic": "professional"},
                {"id": 2, "nodes": ["node_4", "node_5"], "topic": "personal"}
            ],
            "key_entities": ["node_1", "node_3"],
            "bridges": ["node_2"],
            "isolates": []
        }
    
    async def _extract_timeline_data(self, entities: List[Dict[str, Any]], time_window: str) -> List[Dict[str, Any]]:
        """Extract timeline data from entities."""
        timeline_events = []
        
        for entity in entities:
            # Extract timestamped events from entity data
            for category, data in entity.get("data", {}).items():
                if isinstance(data, dict) and "timestamp" in data:
                    timeline_events.append({
                        "entity_id": entity["id"],
                        "category": category,
                        "timestamp": data["timestamp"],
                        "event_type": "data_update",
                        "details": data
                    })
        
        return sorted(timeline_events, key=lambda x: x["timestamp"])
    
    async def _identify_temporal_patterns(self, timeline_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify patterns in timeline data."""
        patterns = []
        
        # Simulate pattern detection
        patterns.append({
            "type": "periodic_activity",
            "frequency": "weekly",
            "confidence": 0.75,
            "entities_involved": ["entity_1", "entity_3"]
        })
        
        patterns.append({
            "type": "burst_activity",
            "timeframe": "2024-01-15 to 2024-01-20",
            "confidence": 0.80,
            "entities_involved": ["entity_2", "entity_4"]
        })
        
        return patterns
    
    async def _detect_temporal_anomalies(self, timeline_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in timeline data."""
        anomalies = []
        
        # Simulate anomaly detection
        anomalies.append({
            "type": "unusual_gap",
            "description": "7-day gap in activity for entity_1",
            "severity": "medium",
            "timestamp": "2024-01-10T00:00:00Z"
        })
        
        return anomalies
    
    async def _predict_temporal_trends(self, timeline_data: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict future temporal trends."""
        predictions = []
        
        # Simulate trend prediction
        predictions.append({
            "type": "activity_increase",
            "confidence": 0.70,
            "timeframe": "next_7_days",
            "entities_affected": ["entity_1", "entity_2"],
            "reasoning": "Based on weekly pattern detection"
        })
        
        return predictions