# OSINT-OS CLI Features

## Overview

The OSINT-OS Command Line Interface (CLI) provides a comprehensive command-line tool for managing OSINT investigations with project creation, research execution, and configuration management. The CLI features intelligence-grade project naming, research intensity levels, and professional project organization.

## Key Features

### 1. Intelligence-Grade Project Naming
- AI-powered generation of intelligence-themed project names
- Multiple naming patterns:
  - Adjective-Operation: `operation_silent_scan_a1b2c3`
  - Intelligence Codes: `operation_neuralweb_x9y8z7`
  - Compound Operations: `operation_vigil_scan_y3cm07`
  - Code-Operation: `operation_darkweb_watch_1a2b3c`
  - Adjective-Code: `operation_cyber_pulse_4d5e6f`
- Unique name validation to prevent conflicts
- Hex identifiers for uniqueness

### 2. Project Structure Organization
- Creates professional project directories with:
  - `data/` - Raw data collected during investigation
  - `docs/` - Documentation and notes
  - `logs/` - Investigation logs and audit trails
  - `outputs/` - Final reports and outputs
- Automatic `config.json` for project configuration
- Professional `README.md` with project details

### 3. Research Intensity Levels
- **Basic**: Surface-level investigation with minimal data collection
- **Standard**: Comprehensive investigation with moderate depth
- **Comprehensive**: Deep investigation with extensive data collection
- **Deep**: Maximum depth investigation with all available resources

### 4. Output Format Options
- JSON: Structured data format for integration
- Markdown: Human-readable reports
- Both: Both formats for maximum flexibility

## Commands

### `research` - Start a new investigation
```bash
python osint_cli.py research "Topic to investigate" --intensity comprehensive --output both
```

Options:
- `--intensity`: Research intensity level [basic|standard|comprehensive|deep]
- `--output`: Output format [json|markdown|both]
- `--project`: Use existing project directory
- `--name`: Custom project name

### `setup` - Create a new project
```bash
python osint_cli.py setup --intensity standard --output both --name "operation_custom_name"
```

Options:
- `--intensity`: Default research intensity level
- `--output`: Default output format
- `--name`: Custom project name

### `projects` - List all projects
```bash
python osint_cli.py projects
```

### `status` - Show project status
```bash
python osint_cli.py status operation_neuralweb_a1b2c3
```

### `config` - Manage configuration
```bash
python osint_cli.py config --list
python osint_cli.py config --set OSINT_API_KEY "your_key"
```

## Usage Examples

### Start a new investigation with comprehensive intensity:
```bash
python osint_cli.py research "Advaned persistent threat analysis" --intensity comprehensive --output both
```

### Create a project for later use:
```bash
python osint_cli.py setup --name "operation_custom_analysis" --intensity deep
```

### List all ongoing investigations:
```bash
python osint_cli.py projects
```

### Check the status of a specific investigation:
```bash
python osint_cli.py status operation_neuralweb_a1b2c3
```

## Integration

The CLI seamlessly integrates with the existing OSINT OS architecture:
- Uses the `OSINTOperatingSystem` class for investigation execution
- Leverages existing workflow and agent systems
- Maintains compatibility with adaptive research capabilities
- Supports all existing API configurations and settings

## Architecture

The CLI follows a modular design with clear separation of concerns:
- Project management handles directory creation and organization
- Research execution orchestrates the investigation workflow
- Configuration management handles environment settings
- Status tracking provides real-time progress updates
