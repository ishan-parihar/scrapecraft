"""
Output Manager for OSINT System

Handles structured output generation, logging, and audit trail management.
Provides comprehensive visibility into system performance and results.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class OutputManager:
    """
    Manages OSINT system outputs including reports, logs, and audit trails.
    """
    
    def __init__(self, base_output_dir: str = None):
        """Initialize the output manager."""
        if base_output_dir is None:
            # Default to ai_agent/outputs directory
            current_dir = Path(__file__).parent.parent.parent
            self.base_dir = current_dir / "outputs"
        else:
            self.base_dir = Path(base_output_dir)
        
        # Create directory structure
        self.reports_dir = self.base_dir / "reports"
        self.logs_dir = self.base_dir / "logs"
        self.audit_dir = self.base_dir / "audit_trail"
        
        for dir_path in [self.reports_dir, self.logs_dir, self.audit_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        self.logger = logging.getLogger(f"{__name__}.OutputManager")
        self.logger.info("Output Manager initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging configuration."""
        # Create timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main system log
        log_file = self.logs_dir / f"osint_system_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console
            ]
        )
    
    def save_investigation_report(
        self, 
        investigation_data: Dict[str, Any], 
        case_id: str = None
    ) -> str:
        """
        Save complete investigation report in structured format.
        
        Args:
            investigation_data: Complete investigation results
            case_id: Optional case ID for filename
            
        Returns:
            Path to saved report file
        """
        if case_id is None:
            case_id = f"investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"{case_id}_report_{timestamp}.json"
        
        # Add metadata
        investigation_data["report_metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "case_id": case_id,
            "report_version": "1.0",
            "output_format": "json"
        }
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(investigation_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Investigation report saved: {report_file}")
        
        # Also save human-readable version
        self.save_human_readable_report(investigation_data, case_id, timestamp)
        
        return str(report_file)
    
    def save_human_readable_report(
        self, 
        investigation_data: Dict[str, Any], 
        case_id: str, 
        timestamp: str
    ):
        """Save human-readable version of the report."""
        report_file = self.reports_dir / f"{case_id}_report_{timestamp}.md"
        
        # Generate markdown report
        markdown_content = self.generate_markdown_report(investigation_data, case_id)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Human-readable report saved: {report_file}")
    
    def generate_markdown_report(self, data: Dict[str, Any], case_id: str) -> str:
        """Generate markdown format report."""
        md_content = f"""# OSINT Investigation Report

**Case ID:** {case_id}  
**Generated:** {data.get('report_metadata', {}).get('generated_at', 'Unknown')}  
**Status:** {data.get('overall_status', 'Unknown')}

---

## Executive Summary

{data.get('intelligence', {}).get('executive_summary', 'No executive summary available.')}

---

## Key Findings

"""
        
        # Add key findings
        key_findings = data.get('intelligence', {}).get('key_findings', [])
        for i, finding in enumerate(key_findings, 1):
            md_content += f"""### Finding {i}
**Significance:** {finding.get('significance', 'Unknown')}  
**Confidence:** {finding.get('confidence', 0):.2f}  
**Description:** {finding.get('description', 'No description available.')}

"""
        
        # Add insights
        insights = data.get('intelligence', {}).get('insights', [])
        if insights:
            md_content += """## Intelligence Insights

"""
            for i, insight in enumerate(insights, 1):
                md_content += f"""### Insight {i}
**Category:** {insight.get('category', 'Unknown')}  
**Confidence:** {insight.get('confidence', 0):.2f}  
**Description:** {insight.get('description', 'No description available.')}

"""
        
        # Add quality assessment
        qa_data = data.get('quality_assessment', {})
        if qa_data:
            md_content += f"""## Quality Assessment

**Overall Quality Score:** {qa_data.get('overall_quality_score', 0):.2f}  
**Quality Grade:** {qa_data.get('quality_grade', 'N/A')}  

### Quality Metrics
"""
            qa_metrics = qa_data.get('quality_metrics', {})
            for metric, value in qa_metrics.items():
                md_content += f"- **{metric.replace('_', ' ').title()}:** {value:.2f}\n"
            
            md_content += f"""
### Threshold Compliance
"""
            thresholds = qa_data.get('quality_thresholds_met', {})
            for threshold, met in thresholds.items():
                status = "✅ PASS" if met else "❌ FAIL"
                md_content += f"- **{threshold.replace('_', ' ').title()}:** {status}\n"
        
        # Add entities and relationships
        fused_data = data.get('fused_data', {})
        if fused_data:
            md_content += """## Entity Analysis

### Identified Entities
"""
            entities = fused_data.get('entities', [])
            for entity in entities:
                md_content += f"""- **{entity.get('name', 'Unknown')}** ({entity.get('type', 'Unknown')})
  - Confidence: {entity.get('confidence', 0):.2f}
  - Sources: {', '.join(entity.get('sources', []))}
"""
            
            relationships = fused_data.get('relationships', [])
            if relationships:
                md_content += """
### Entity Relationships
"""
                for rel in relationships:
                    md_content += f"""- **{rel.get('source', 'Unknown')}** → **{rel.get('target', 'Unknown')}** ({rel.get('type', 'Unknown')})
  - Confidence: {rel.get('confidence', 0):.2f}
"""
        
        # Add patterns
        patterns = data.get('patterns', [])
        if patterns:
            md_content += """## Pattern Analysis

"""
            for pattern in patterns:
                md_content += f"""### {pattern.get('type', 'Unknown Pattern').replace('_', ' ').title()}
**Significance:** {pattern.get('significance', 'Unknown')}  
**Confidence:** {pattern.get('confidence', 0):.2f}  
**Description:** {pattern.get('description', 'No description available.')}

"""
        
        md_content += """---

## Report Metadata

"""
        metadata = data.get('report_metadata', {})
        for key, value in metadata.items():
            md_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        
        md_content += f"""

---

*Report generated by OSINT System v1.0*  
*For questions or clarification, contact the system administrator*
"""
        
        return md_content
    
    def log_agent_execution(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any],
        execution_time: float,
        success: bool,
        error_message: str = None
    ):
        """Log agent execution for audit trail."""
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "agent_name": agent_name,
            "success": success,
            "execution_time_seconds": execution_time,
            "input_summary": self.summarize_data(input_data),
            "output_summary": self.summarize_data(output_data),
            "error_message": error_message
        }
        
        # Save to audit trail
        audit_file = self.audit_dir / f"agent_execution_log_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Read existing logs or create new
        if audit_file.exists():
            with open(audit_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(audit_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        # Also log to standard logger
        if success:
            self.logger.info(f"Agent {agent_name} executed successfully in {execution_time:.2f}s")
        else:
            self.logger.error(f"Agent {agent_name} failed: {error_message}")
    
    def summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of data for logging."""
        summary = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                summary[key] = f"string ({len(value)} chars)"
            elif isinstance(value, list):
                summary[key] = f"list ({len(value)} items)"
            elif isinstance(value, dict):
                summary[key] = f"dict ({len(value)} keys)"
            else:
                summary[key] = type(value).__name__
        
        return summary
    
    def get_latest_reports(self, limit: int = 5) -> list:
        """Get list of latest reports."""
        reports = []
        
        for file_path in self.reports_dir.glob("*.json"):
            stat = file_path.stat()
            reports.append({
                "file": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # Sort by modified time (newest first)
        reports.sort(key=lambda x: x["modified"], reverse=True)
        
        return reports[:limit]
    
    def get_audit_logs(self, date: str = None) -> list:
        """Get audit logs for specific date."""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        audit_file = self.audit_dir / f"agent_execution_log_{date}.json"
        
        if audit_file.exists():
            with open(audit_file, 'r') as f:
                return json.load(f)
        
        return []


# Global output manager instance
_output_manager = None

def get_output_manager() -> OutputManager:
    """Get global output manager instance."""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager