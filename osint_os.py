#!/usr/bin/env python3
"""
Main OSINT Operating System Interface

The central entry point for the OSINT/SOCMINT investigation platform.
This script provides a unified command interface to orchestrate
complete investigations from start to finish with persistent state management.
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow, OSINTWorkflow
from ai_agent.src.workflow.state import (
    create_initial_state, 
    InvestigationPhase, 
    InvestigationStatus,
    InvestigationState
)
from ai_agent.src.agents.synthesis.enhanced_report_generation_agent_v2 import EnhancedReportGenerationAgentV2


class OSINTOperatingSystem:
    """
    The main OSINT Operating System interface that orchestrates
    the entire investigation lifecycle.
    """
    
    def __init__(self):
        self.workflow: Optional[OSINTWorkflow] = None
        self.state: Optional[InvestigationState] = None
        self.logger = None
        
    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the OSINT Operating System."""
        print("Initializing OSINT Operating System...")
        
        # Create the workflow orchestrator
        self.workflow = create_osint_workflow(config or {})
        print("✓ OSINT workflow initialized")
        
        # Setup logging
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("osint_os")
        print("✓ Logging system initialized")
        
        print("OSINT Operating System ready!")
        
    def create_investigation(
        self, 
        user_request: str,
        investigation_id: Optional[str] = None,
        priority: str = "medium"
    ) -> InvestigationState:
        """Create a new investigation state."""
        if not self.workflow:
            raise RuntimeError("OSINT Operating System not initialized")
            
        state = create_initial_state(
            user_request=user_request,
            investigation_id=investigation_id,
            initiator="osint_cli",
            priority=priority
        )
        
        self.state = state
        return state
        
    async def run_investigation(
        self, 
        user_request: str,
        investigation_id: Optional[str] = None,
        priority: str = "medium"
    ) -> InvestigationState:
        """Run a complete OSINT investigation."""
        if not self.workflow:
            raise RuntimeError("OSINT Operating System not initialized")
            
        # Create investigation state
        state = self.create_investigation(user_request, investigation_id, priority)
        
        print(f"Starting investigation: {state['investigation_id']}")
        print(f"Request: {state['user_request']}")
        print("-" * 60)
        
        # Execute the complete investigation workflow
        final_state = await self.workflow.run_investigation(
            user_request=user_request,
            investigation_id=state["investigation_id"]
        )
        
        self.state = final_state
        return final_state
        
    async def get_progress(self) -> Dict[str, Any]:
        """Get current investigation progress."""
        if not self.workflow or not self.state:
            return {"error": "No active investigation"}
            
        progress = self.workflow.get_investigation_progress(self.state)
        return progress
        
    def save_state(self, filename: str):
        """Save the current investigation state to a file."""
        if not self.state:
            raise RuntimeError("No investigation state to save")
            
        with open(filename, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)  # default=str handles datetime objects
            
        print(f"Investigation state saved to: {filename}")
        
    def load_state(self, filename: str):
        """Load an investigation state from a file."""
        with open(filename, 'r') as f:
            self.state = json.load(f)
            
        print(f"Investigation state loaded from: {filename}")
        
    async def generate_report(self, output_format: str = "json") -> str:
        """Generate a final report from the investigation."""
        if not self.state:
            raise RuntimeError("No investigation state available")
            
        # Prepare report generation input
        report_input = {
            "intelligence": self.state.get("intelligence", {}),
            "quality_assessment": self.state.get("quality_assessment", {}),
            "fused_data": self.state.get("fused_data", {}),
            "patterns": self.state.get("patterns", []),
            "context_analysis": self.state.get("context_analysis", {}),
            "sources_used": self.state.get("sources_used", []),
            "user_request": self.state.get("user_request", ""),
            "objectives": self.state.get("objectives", {}),
            "investigation_metadata": {
                "case_id": self.state.get("investigation_id", "unknown"),
                "start_time": self.state.get("initiated_at", "unknown"),
                "investigator": "OSINT System"
            }
        }
        
        # Create report generation agent and execute
        agent = EnhancedReportGenerationAgentV2()
        result = await agent.execute(report_input)
        
        if not result.success:
            raise RuntimeError(f"Report generation failed: {result.error_message}")
            
        report_data = result.data
        report_content = report_data.get("primary_report", {})
        
        # Format output based on requested format
        if output_format == "json":
            return json.dumps(report_content, indent=2)
        elif output_format == "text":
            # Create a text-based report
            text_report = f"""
OSINT Investigation Report
==========================

Investigation ID: {self.state.get('investigation_id', 'N/A')}
User Request: {self.state.get('user_request', 'N/A')}
Status: {self.state.get('overall_status', 'N/A')}
Confidence: {self.state.get('confidence_level', 0.0):.2f}

Summary of Findings:
{json.dumps(report_content, indent=2)}
"""
            return text_report
        else:
            return json.dumps(report_content, indent=2)


async def main():
    """Main command line interface for the OSINT Operating System."""
    parser = argparse.ArgumentParser(
        description="OSINT Operating System - Advanced Investigation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --request "Research John Doe in New York"
  %(prog)s --request "Investigate company ABC Corp" --priority high
  %(prog)s --load-state saved_inv.json --report
        """
    )
    
    parser.add_argument(
        "--request", 
        type=str, 
        help="The investigation request to execute"
    )
    
    parser.add_argument(
        "--priority", 
        type=str, 
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Priority level for the investigation"
    )
    
    parser.add_argument(
        "--load-state", 
        type=str,
        help="Load a saved investigation state from file"
    )
    
    parser.add_argument(
        "--save-state", 
        type=str,
        help="Save current investigation state to file"
    )
    
    parser.add_argument(
        "--report", 
        action="store_true",
        help="Generate a final report after investigation"
    )
    
    parser.add_argument(
        "--report-format", 
        type=str,
        default="json",
        choices=["json", "text"],
        help="Format for the generated report"
    )
    
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Run in interactive mode with step-by-step execution"
    )
    
    args = parser.parse_args()
    
    # Create OSINT Operating System instance
    osint_os = OSINTOperatingSystem()
    
    try:
        # Initialize the system
        await osint_os.initialize()
        
        # Handle state loading
        if args.load_state:
            print(f"Loading investigation state from: {args.load_state}")
            osint_os.load_state(args.load_state)
            
            if args.report:
                # Generate report from loaded state
                report = await osint_os.generate_report(args.report_format)
                output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.report_format}"
                with open(output_file, 'w') as f:
                    f.write(report)
                print(f"Report generated and saved to: {output_file}")
                
        elif args.request:
            # Run a new investigation
            print(f"Starting investigation: {args.request}")
            
            if args.interactive:
                print("\nInteractive mode - investigating step by step...")
                
                # In interactive mode, we could potentially pause between phases
                # For now, just run normally but with more verbose output
                pass
            
            # Execute the investigation
            final_state = await osint_os.run_investigation(
                user_request=args.request,
                priority=args.priority
            )
            
            # Show results
            progress = await osint_os.get_progress()
            print(f"\nInvestigation completed!")
            print(f"Status: {progress['overall_status']}")
            print(f"Progress: {progress['progress_percentage']:.1f}%")
            print(f"Confidence: {progress['confidence_level']:.2f}")
            print(f"Errors: {progress['errors_count']}")
            print(f"Sources used: {progress['sources_used']}")
            
            # Save state if requested
            if args.save_state:
                osint_os.save_state(args.save_state)
                
            # Generate report if requested
            if args.report:
                print("\nGenerating final report...")
                report = await osint_os.generate_report(args.report_format)
                output_file = f"investigation_report_{final_state['investigation_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.report_format}"
                
                with open(output_file, 'w') as f:
                    f.write(report)
                    
                print(f"Report generated and saved to: {output_file}")
                
        else:
            # No arguments provided - show help
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nInvestigation interrupted by user")
        if osint_os.state and args.save_state:
            print(f"Saving current state to: {args.save_state}")
            osint_os.save_state(args.save_state)
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())