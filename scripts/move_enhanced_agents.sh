#!/bin/bash

# Script to move enhanced agents to the proper location in the synthesis directory

echo "Moving enhanced agents to proper location..."

# Check if source files exist
if [ ! -f "enhanced_intelligence_synthesis_agent_v2.py" ]; then
    echo "Error: enhanced_intelligence_synthesis_agent_v2.py not found in current directory"
    exit 1
fi

if [ ! -f "enhanced_report_generation_agent_v2.py" ]; then
    echo "Error: enhanced_report_generation_agent_v2.py not found in current directory"
    exit 1
fi

# Check if target directory exists and is writable
TARGET_DIR="ai_agent/src/agents/synthesis"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory $TARGET_DIR does not exist"
    exit 1
fi

# Move the files
echo "Moving enhanced_intelligence_synthesis_agent_v2.py to $TARGET_DIR..."
cp "enhanced_intelligence_synthesis_agent_v2.py" "$TARGET_DIR/" &&
echo "Successfully moved enhanced_intelligence_synthesis_agent_v2.py"

echo "Moving enhanced_report_generation_agent_v2.py to $TARGET_DIR..."
cp "enhanced_report_generation_agent_v2.py" "$TARGET_DIR/" &&
echo "Successfully moved enhanced_report_generation_agent_v2.py"

# Update the __init__.py file in the synthesis directory
INIT_FILE="$TARGET_DIR/__init__.py"

echo "Updating $INIT_FILE with new agent imports..."

# Create a backup
cp "$INIT_FILE" "$INIT_FILE.bak"
echo "Created backup: $INIT_FILE.bak"

# Add imports to the __init__.py file
cat > "$TARGET_DIR/__init__.py.new" << 'EOF'
"""
Synthesis Phase Agents

This package contains agents for the synthesis phase of OSINT investigations:
- IntelligenceSynthesisAgent: Combines analysis results into actionable intelligence
- QualityAssuranceAgent: Validates data quality and analysis accuracy
- ReportGenerationAgent: Creates comprehensive investigation reports
- EnhancedIntelligenceSynthesisAgentV2: Enhanced version with mandatory source link verification
- EnhancedReportGenerationAgentV2: Enhanced version with mandatory source link verification
"""

from .intelligence_synthesis_agent import IntelligenceSynthesisAgent
from .quality_assurance_agent import QualityAssuranceAgent
from .report_generation_agent import ReportGenerationAgent
from .quality_assurance_agent_v2 import QualityAssuranceAgentV2
from .enhanced_intelligence_synthesis_agent_v2 import EnhancedIntelligenceSynthesisAgentV2
from .enhanced_report_generation_agent_v2 import EnhancedReportGenerationAgentV2

__all__ = [
    "IntelligenceSynthesisAgent",
    "QualityAssuranceAgent", 
    "ReportGenerationAgent",
    "QualityAssuranceAgentV2",
    "EnhancedIntelligenceSynthesisAgentV2",
    "EnhancedReportGenerationAgentV2"
]
EOF

# Replace the original file
mv "$TARGET_DIR/__init__.py.new" "$INIT_FILE"
echo "Successfully updated $INIT_FILE"

echo "All enhanced agents have been moved and imports updated!"
echo "Note: You may need to run 'chmod +x move_enhanced_agents.sh' and fix file permissions before executing this script."