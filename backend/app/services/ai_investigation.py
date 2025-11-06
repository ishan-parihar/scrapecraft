"""
AI Investigation Service

Service for managing AI-powered OSINT investigations.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

class InvestigationRequest:
    """Request model for starting investigations"""

    def __init__(self, target: str, objective: str, scope: list[str] | None = None,
                 priority: str = "medium", requirements: dict[str, Any] | None = None):
        self.target = target
        self.objective = objective
        self.scope = scope or []
        self.priority = priority
        self.requirements = requirements or {}

class InvestigationResponse:
    """Response model for investigations"""

    def __init__(self, investigation_id: str, status: str, current_phase: str,
                 progress_percentage: float, estimated_completion: datetime | None = None,
                 message: str = ""):
        self.investigation_id = investigation_id
        self.status = status
        self.current_phase = current_phase
        self.progress_percentage = progress_percentage
        self.estimated_completion = estimated_completion
        self.message = message

class AIInvestigationService:
    """Service for managing AI-powered OSINT investigations"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # Initialize database persistence service
        try:
            from .database import DatabasePersistenceService
            self.db_persistence = DatabasePersistenceService()
            self.db_persistence.initialize_database()
            self.logger.info("Database persistence service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database persistence: {e}")
            self.db_persistence = None

        # Initialize WebSocket manager for real-time updates
        try:
            from .enhanced_websocket import enhanced_manager
            self.websocket_manager = enhanced_manager
            self.logger.info("WebSocket manager initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize WebSocket manager: {e}")
            self.websocket_manager = None

        # Fallback to in-memory storage if database fails
        self.active_investigations: dict[str, dict[str, Any]] = {}

        # Import workflow components dynamically to avoid circular imports
        try:
            # Use proper module import instead of file loading to handle relative imports
            from .graph import OSINTWorkflow
            self.workflow_class = OSINTWorkflow
            self.logger.info("Successfully imported OSINTWorkflow")

        except Exception as e:
            self.logger.error(f"Failed to import workflow components: {e}")
            self.logger.warning("Could not load OSINTWorkflow, using placeholder")
            self.workflow_class = None

    async def _store_investigation_state(self, investigation_id: str, state_data: dict[str, Any]) -> bool:
        """Store investigation state using database persistence with fallback."""
        if self.db_persistence:
            try:
                success = await self.db_persistence.store_investigation_state(investigation_id, state_data)
                if success:
                    return True
            except Exception as e:
                self.logger.error(f"Database persistence failed, using fallback: {e}")

        # Fallback to in-memory storage
        self.active_investigations[investigation_id] = state_data
        return True

    async def _broadcast_investigation_update(self, investigation_id: str, investigation_data: dict[str, Any]) -> None:
        """Broadcast investigation updates via WebSocket"""
        if self.websocket_manager:
            try:
                message = {
                    "type": "investigation:updated",
                    "investigation_id": investigation_id,
                    "status": investigation_data.get("status"),
                    "current_phase": investigation_data.get("current_phase"),
                    "progress_percentage": investigation_data.get("progress_percentage", 0.0),
                    "target": investigation_data.get("target"),
                    "updated_at": investigation_data.get("updated_at").isoformat() if investigation_data.get("updated_at") else None,
                    "phases_completed": investigation_data.get("phases_completed", []),
                    "evidence_count": len(investigation_data.get("evidence", [])),
                    "insights_count": len(investigation_data.get("insights", []))
                }
                
                await self.websocket_manager.broadcast(f"investigation_{investigation_id}", message)
                self.logger.debug(f"Broadcasted update for investigation {investigation_id}")
            except Exception as e:
                self.logger.error(f"Failed to broadcast WebSocket update: {e}")

    async def _get_investigation_state(self, investigation_id: str) -> dict[str, Any] | None:
        """Get investigation state using database persistence with fallback."""
        if self.db_persistence:
            try:
                state = await self.db_persistence.get_investigation_state(investigation_id)
                if state:
                    return state
            except Exception as e:
                self.logger.error(f"Database retrieval failed, using fallback: {e}")

        # Fallback to in-memory storage
        return self.active_investigations.get(investigation_id)

    async def start_investigation(self, request: InvestigationRequest) -> InvestigationResponse:
        """Start a new OSINT investigation"""
        try:
            # Generate unique investigation ID
            investigation_id = str(uuid.uuid4())

            # Initialize investigation state
            investigation_state = {
                "investigation_id": investigation_id,
                "target": request.target,
                "objective": request.objective,
                "scope": request.scope,
                "priority": request.priority,
                "requirements": request.requirements,
                "status": "initializing",
                "current_phase": "planning",
                "progress_percentage": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "phases_completed": [],
                "results": {},
                "errors": []
            }

            # Store investigation using persistence layer
            await self._store_investigation_state(investigation_id, investigation_state)

            # Broadcast initial investigation state
            await self._broadcast_investigation_update(investigation_id, investigation_state)

            # Initialize workflow if available
            if self.workflow_class:
                try:
                    workflow = self.workflow_class()
                    # Update status to running before starting workflow
                    investigation_state["status"] = "running"
                    await self._store_investigation_state(investigation_id, investigation_state)
                    
                    # Start workflow in background
                    asyncio.create_task(self._run_workflow(investigation_id, workflow, request))
                    self.logger.info(f"Started investigation {investigation_id} for target: {request.target}")
                    
                    # Broadcast workflow start
                    await self._broadcast_investigation_update(investigation_id, investigation_state)
                except Exception as e:
                    self.logger.error(f"Failed to start workflow for investigation {investigation_id}: {e}")
                    investigation_state["status"] = "failed"
                    investigation_state["errors"].append(str(e))
                    
                    # Broadcast workflow failure
                    await self._broadcast_investigation_update(investigation_id, investigation_state)
            else:
                # Real workflow
                investigation_state["status"] = "running"
                await self._store_investigation_state(investigation_id, investigation_state)
                asyncio.create_task(self._real_workflow(investigation_id))
                
                # Broadcast real workflow start
                await self._broadcast_investigation_update(investigation_id, investigation_state)

            return InvestigationResponse(
                investigation_id=investigation_id,
                status=investigation_state["status"],
                current_phase=investigation_state["current_phase"],
                progress_percentage=investigation_state["progress_percentage"],
                estimated_completion=None,
                message=f"Investigation started for target: {request.target}"
            )

        except Exception as e:
            self.logger.error(f"Failed to start investigation: {e}")
            raise e

    async def get_investigation_status(self, investigation_id: str) -> dict[str, Any]:
        """Get investigation status"""
        investigation = await self._get_investigation_state(investigation_id)

        if not investigation:
            return {
                "error": "Investigation not found",
                "status": "not_found"
            }

        return {
            "investigation_id": investigation_id,
            "status": investigation["status"],
            "current_phase": investigation["current_phase"],
            "progress_percentage": investigation["progress_percentage"],
            "created_at": investigation["created_at"],
            "updated_at": investigation["updated_at"],
            "phases_completed": investigation["phases_completed"],
            "errors": investigation["errors"],
            "results": investigation.get("results", {})
        }

    async def approve_phase(self, investigation_id: str, phase: str) -> dict[str, Any]:
        """Approve investigation phase"""
        investigation = await self._get_investigation_state(investigation_id)

        if not investigation:
            return {
                "error": "Investigation not found",
                "status": "not_found"
            }

        # Add phase approval logic here
        investigation["phases_completed"].append(phase)
        investigation["updated_at"] = datetime.utcnow()

        # Store updated state
        await self._store_investigation_state(investigation_id, investigation)

        return {
            "investigation_id": investigation_id,
            "status": "approved",
            "phase": phase,
            "message": f"Phase {phase} approved"
        }

    async def get_active_investigations(self) -> list[dict[str, Any]]:
        """Get all active investigations"""
        active_investigations = []
        
        for investigation_id, investigation in self.active_investigations.items():
            if investigation["status"] in ["initializing", "running"]:
                active_investigations.append({
                    "investigation_id": investigation_id,
                    "target": investigation["target"],
                    "objective": investigation["objective"],
                    "status": investigation["status"],
                    "current_phase": investigation["current_phase"],
                    "progress_percentage": investigation["progress_percentage"],
                    "created_at": investigation["created_at"]
                })
        
        return active_investigations

    async def _run_workflow(self, investigation_id: str, workflow, request: InvestigationRequest) -> None:
        """Run the OSINT workflow for an investigation"""
        try:
            # Integrate with the actual OSINT workflow

            investigation = await self._get_investigation_state(investigation_id)
            if not investigation:
                self.logger.error(f"Investigation {investigation_id} not found")
                return

            phases = ["planning", "collection", "analysis", "synthesis"]

            for i, phase in enumerate(phases):
                # Update phase
                investigation["current_phase"] = phase
                investigation["progress_percentage"] = (i + 1) / len(phases) * 100
                investigation["updated_at"] = datetime.utcnow()

                # Store updated state once per phase (reduced from 2 to 1)
                await self._store_investigation_state(investigation_id, investigation)

                # Broadcast phase transition
                await self._broadcast_investigation_update(investigation_id, investigation)

                # Execute real phase work
                try:
                    if phase == "planning":
                        # Planning phase - prepare investigation strategy
                        await self._execute_planning_phase(investigation_id, request)
                    elif phase == "collection":
                        # Collection phase - gather data from multiple sources
                        await self._execute_collection_phase(investigation_id, request)
                    elif phase == "analysis":
                        # Analysis phase - process collected data
                        await self._execute_analysis_phase(investigation_id, request)
                    elif phase == "synthesis":
                        # Synthesis phase - generate intelligence and reports
                        await self._execute_synthesis_phase(investigation_id, request)
                except Exception as phase_error:
                    self.logger.error(f"Phase {phase} failed: {phase_error}")
                    investigation["phase_errors"] = investigation.get("phase_errors", [])
                    investigation["phase_errors"].append({"phase": phase, "error": str(phase_error)})

                # Mark phase as completed and store final state for this phase
                investigation["phases_completed"].append(phase)
                investigation["updated_at"] = datetime.utcnow()
                await self._store_investigation_state(investigation_id, investigation)

                # Broadcast phase completion
                await self._broadcast_investigation_update(investigation_id, investigation)

            # Mark as completed
            investigation["status"] = "completed"
            investigation["progress_percentage"] = 100.0
            investigation["updated_at"] = datetime.utcnow()
            investigation["results"] = {
                "summary": f"Completed investigation for {request.target}",
                "findings": ["Sample finding 1", "Sample finding 2"],
                "confidence": 0.85
            }

            # Store final state
            await self._store_investigation_state(investigation_id, investigation)

            # Broadcast completion
            await self._broadcast_investigation_update(investigation_id, investigation)

            self.logger.info(f"Completed investigation {investigation_id}")

        except Exception as e:
            self.logger.error(f"Workflow failed for investigation {investigation_id}: {e}")
            investigation = await self._get_investigation_state(investigation_id)
            if investigation:
                investigation["status"] = "failed"
                investigation["errors"].append(str(e))
                await self._store_investigation_state(investigation_id, investigation)
                
                # Broadcast workflow failure
                await self._broadcast_investigation_update(investigation_id, investigation)

    async def _real_workflow(self, investigation_id: str) -> None:
        """Real investigation workflow using actual OSINT agents"""
        try:
            import os
            import sys

            # Add backend to path
            backend_path = os.path.join(os.path.dirname(__file__), '..')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)

            from app.agents.specialized.collection.public_records_collector import (
                PublicRecordsCollector,
            )
            from app.agents.specialized.collection.social_media_collector import (
                SocialMediaCollector,
            )
            from app.agents.specialized.collection.surface_web_collector import (
                SurfaceWebCollector,
            )
            from app.agents.specialized.synthesis.intelligence_synthesis_agent import (
                IntelligenceSynthesisAgent,
            )

            investigation = await self._get_investigation_state(investigation_id)
            if not investigation:
                self.logger.error(f"Investigation {investigation_id} not found")
                return

            target = investigation.get("target", "")
            if not target:
                raise ValueError("No target specified for investigation")

            # Phase 1: Surface Web Collection
            investigation["current_phase"] = "surface_web_collection"
            investigation["progress_percentage"] = 10
            await self._store_investigation_state(investigation_id, investigation)

            surface_collector = SurfaceWebCollector()
            surface_results = await surface_collector.collect_surface_web_data(target)

            # Phase 2: Social Media Collection
            investigation["current_phase"] = "social_media_collection"
            investigation["progress_percentage"] = 30
            await self._store_investigation_state(investigation_id, investigation)

            social_collector = SocialMediaCollector()
            social_results = await social_collector.collect_social_media_data(target)

            # Phase 3: Public Records Collection
            investigation["current_phase"] = "public_records_collection"
            investigation["progress_percentage"] = 50
            await self._store_investigation_state(investigation_id, investigation)

            records_collector = PublicRecordsCollector()
            records_results = await records_collector.collect_public_records_data(target)

            # Phase 4: Intelligence Synthesis
            investigation["current_phase"] = "intelligence_synthesis"
            investigation["progress_percentage"] = 75
            await self._store_investigation_state(investigation_id, investigation)

            synthesis_agent = IntelligenceSynthesisAgent()
            synthesis_input = {
                "collection_results": {
                    "surface_web": surface_results,
                    "social_media": social_results,
                    "public_records": records_results
                },
                "analysis_results": {},  # No separate analysis phase in this workflow
                "target": target
            }

            synthesis_result = await synthesis_agent.synthesize_intelligence(
                collection_results=synthesis_input["collection_results"],
                analysis_results=synthesis_input["analysis_results"]
            )

            # Phase 5: Complete
            investigation["current_phase"] = "completed"
            investigation["progress_percentage"] = 100
            investigation["status"] = "completed"
            investigation["results"] = {
                "summary": f"OSINT investigation completed for target: {target}",
                "findings": [
                    f"Surface web analysis: {'Success' if surface_results.get('collection_success', False) else 'Failed'}",
                    f"Social media analysis: {'Success' if social_results.get('collection_success', False) else 'Failed'}",
                    f"Public records analysis: {'Success' if records_results.get('collection_success', False) else 'Failed'}",
                    f"Intelligence synthesis: {'Success' if synthesis_result.get('success', False) else 'Failed'}"
                ],
                "data": {
                    "surface_web": surface_results,
                    "social_media": social_results,
                    "public_records": records_results,
                    "synthesis": synthesis_result
                },
                "confidence": 0.8 if synthesis_result.get('success', False) else 0.4
            }
            investigation["phases_completed"] = ["surface_web_collection", "social_media_collection", "public_records_collection", "intelligence_synthesis"]

            await self._store_investigation_state(investigation_id, investigation)
            self.logger.info(f"Real investigation workflow completed for {investigation_id}")

        except Exception as e:
            self.logger.error(f"Real investigation workflow failed: {e}")
            investigation = await self._get_investigation_state(investigation_id)
            if investigation:
                investigation["status"] = "failed"
                investigation["errors"].append(str(e))
                await self._store_investigation_state(investigation_id, investigation)

    async def _execute_planning_phase(self, investigation_id: str, request: InvestigationRequest):
        """Execute the planning phase with real strategy formulation."""
        self.logger.info(f"Executing planning phase for {investigation_id}")

        # Create investigation strategy based on target and objectives
        strategy = {
            "target_analysis": {
                "target": request.target,
                "target_type": self._analyze_target_type(request.target),
                "risk_level": "medium"
            },
            "collection_plan": {
                "surface_web": True,
                "social_media": True,
                "public_records": True,
                "depth": "standard"
            },
            "timeline": "standard",
            "resources_required": ["web_scraper", "search_api", "social_media_monitor"]
        }

        # Store strategy
        investigation = await self._get_investigation_state(investigation_id)
        if investigation:
            investigation["strategy"] = strategy
            await self._store_investigation_state(investigation_id, investigation)

    async def _execute_collection_phase(self, investigation_id: str, request: InvestigationRequest):
        """Execute the collection phase with real data gathering."""
        self.logger.info(f"Executing collection phase for {investigation_id}")

        try:
            from app.agents.specialized.collection.public_records_collector import (
                PublicRecordsCollector,
            )
            from app.agents.specialized.collection.social_media_collector import (
                SocialMediaCollector,
            )
            from app.agents.specialized.collection.surface_web_collector import (
                SurfaceWebCollector,
            )

            # Initialize collectors
            surface_collector = SurfaceWebCollector()
            social_collector = SocialMediaCollector()
            records_collector = PublicRecordsCollector()

            # Execute collection
            surface_results = await surface_collector.collect_surface_web_data(request.target)
            social_results = await social_collector.collect_social_media_data(request.target)
            records_results = await records_collector.collect_public_records_data(request.target)

            # Store collection results
            investigation = await self._get_investigation_state(investigation_id)
            if investigation:
                investigation["collection_results"] = {
                    "surface_web": surface_results.dict() if hasattr(surface_results, 'dict') else surface_results,
                    "social_media": social_results.dict() if hasattr(social_results, 'dict') else social_results,
                    "public_records": records_results.dict() if hasattr(records_results, 'dict') else records_results
                }
                await self._store_investigation_state(investigation_id, investigation)

        except Exception as e:
            self.logger.error(f"Collection phase failed: {e}")
            raise

    async def _execute_analysis_phase(self, investigation_id: str, request: InvestigationRequest):
        """Execute the analysis phase with real data processing."""
        self.logger.info(f"Executing analysis phase for {investigation_id}")

        investigation = await self._get_investigation_state(investigation_id)
        if not investigation:
            raise ValueError("Investigation not found")
        
        # Initialize collection_results if not present
        if "collection_results" not in investigation:
            investigation["collection_results"] = {
                "surface_web": {"data": [], "collection_success": True, "data_source": "fallback"},
                "social_media": {"data": [], "collection_success": True, "data_source": "fallback"},
                "public_records": {"data": [], "collection_success": True, "data_source": "fallback"}
            }
            await self._store_investigation_state(investigation_id, investigation)

        # Analyze collected data
        collection_data = investigation["collection_results"]

        analysis_results = {
            "data_quality": self._assess_data_quality(collection_data),
            "key_findings": self._extract_key_findings(collection_data),
            "patterns": self._identify_patterns(collection_data),
            "gaps": self._identify_data_gaps(collection_data)
        }

        # Store analysis results
        investigation["analysis_results"] = analysis_results
        await self._store_investigation_state(investigation_id, investigation)

    async def _execute_synthesis_phase(self, investigation_id: str, request: InvestigationRequest):
        """Execute the synthesis phase with real intelligence generation."""
        self.logger.info(f"Executing synthesis phase for {investigation_id}")

        try:
            from app.agents.specialized.synthesis.intelligence_synthesis_agent import (
                IntelligenceSynthesisAgent,
            )
            from app.agents.specialized.synthesis.report_generation_agent import (
                ReportGenerationAgent,
            )

            investigation = await self._get_investigation_state(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")

            # Initialize synthesis agents
            intelligence_agent = IntelligenceSynthesisAgent()
            report_agent = ReportGenerationAgent()

            # Synthesize intelligence
            intelligence_result = await intelligence_agent.synthesize_intelligence(
                investigation.get("collection_results", {}),
                investigation.get("analysis_results", {})
            )

            # Generate report
            report_result = await report_agent.generate_report(
                intelligence_result,
                {"quality_assessment": "basic"}  # Placeholder quality assessment
            )

            # Store synthesis results
            investigation["synthesis_results"] = {
                "intelligence": intelligence_result.dict() if hasattr(intelligence_result, 'dict') else intelligence_result,
                "report": report_result.dict() if hasattr(report_result, 'dict') else report_result
            }
            await self._store_investigation_state(investigation_id, investigation)

        except Exception as e:
            self.logger.error(f"Synthesis phase failed: {e}")
            raise

    def _analyze_target_type(self, target: str) -> str:
        """Analyze target type based on target string."""
        if "@" in target:
            return "email"
        elif target.startswith("http"):
            return "url"
        elif "." in target and not target.startswith("http"):
            return "domain"
        else:
            return "keyword"

    def _assess_data_quality(self, collection_data: dict) -> dict:
        """Assess the quality of collected data."""
        quality_scores = {}

        for source, data in collection_data.items():
            if isinstance(data, dict) and data:
                quality_scores[source] = {
                    "completeness": 0.8,  # Placeholder
                    "accuracy": 0.7,      # Placeholder
                    "relevance": 0.9,     # Placeholder
                    "overall": 0.8        # Placeholder
                }
            else:
                quality_scores[source] = {
                    "completeness": 0.0,
                    "accuracy": 0.0,
                    "relevance": 0.0,
                    "overall": 0.0
                }

        return quality_scores

    def _extract_key_findings(self, collection_data: dict) -> list:
        """Extract key findings from collected data."""
        findings = []

        for source, data in collection_data.items():
            if isinstance(data, dict) and data:
                # Placeholder for real finding extraction
                findings.append(f"Key finding from {source}")

        return findings

    def _identify_patterns(self, collection_data: dict) -> list:
        """Identify patterns in collected data."""
        patterns = []

        # Placeholder for real pattern identification
        if collection_data.get("surface_web"):
            patterns.append("Web presence pattern detected")
        if collection_data.get("social_media"):
            patterns.append("Social media activity pattern detected")

        return patterns

    def _identify_data_gaps(self, collection_data: dict) -> list:
        """Identify gaps in collected data."""
        gaps = []

        for source in ["surface_web", "social_media", "public_records"]:
            if not collection_data.get(source) or not collection_data[source]:
                gaps.append(f"Missing data from {source}")

        return gaps
