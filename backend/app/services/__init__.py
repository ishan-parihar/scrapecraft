"""
Services Module

Contains various services for the ScrapeCraft backend.
"""

# Agent structure migration is complete - re-enable LangGraph workflow imports
from .graph import (
    OSINTWorkflow, 
    create_osint_workflow,
    objective_definition_node,
    strategy_formulation_node,
    search_coordination_node,
    data_collection_node,
    data_fusion_node,
    pattern_recognition_node,
    contextual_analysis_node,
    intelligence_synthesis_node,
    quality_assurance_node,
    report_generation_node
)
from .state import InvestigationState

# Basic services that should work
from .database import get_db
from .websocket import ConnectionManager

# File-based task storage (re-enabled with file-based fallback)
from .task_storage import task_storage

__all__ = [
    "OSINTWorkflow",
    "create_osint_workflow", 
    "InvestigationState",
    "objective_definition_node",
    "strategy_formulation_node",
    "search_coordination_node",
    "data_collection_node",
    "data_fusion_node",
    "pattern_recognition_node",
    "contextual_analysis_node",
    "intelligence_synthesis_node",
    "quality_assurance_node",
    "report_generation_node",
    "get_db",
    "ConnectionManager",
    "task_storage"
]