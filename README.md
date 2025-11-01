# OSINT-OS: Advanced OSINT Investigation Platform

OSINT-OS is a comprehensive open-source intelligence (OSINT) investigation platform that enables users to perform systematic research and data collection from public sources.

## Features

- **Modular Architecture**: Clean separation of concerns between CLI, core engine, and services
- **Project-Based Organization**: Automatic project creation with proper directory structure
- **Configurable Intensity Levels**: Basic, standard, comprehensive, and deep investigation modes
- **Multiple Output Formats**: JSON and Markdown report generation
- **Robust Logging**: Comprehensive logging to both console and project-specific files
- **State Management**: Ability to save and restore investigation states

## Architecture

- `osint_cli.py`: Main command-line interface with project management capabilities
- `osint_os.py`: Core OSINT operating system engine
- Project directories: Automatically created with `data/`, `docs/`, `logs/`, and `outputs/` subdirectories

## Commands

### Create a new investigation:
```bash
python osint_cli.py research "Your investigation topic"
```

### Create a project without starting investigation:
```bash
python osint_cli.py setup "Your investigation topic"
```

### List existing projects:
```bash
python osint_cli.py projects
```

### Check project status:
```bash
python osint_cli.py status /path/to/project
```

### Manage configuration:
```bash
python osint_cli.py config
```

## Project Structure

Each investigation project automatically gets the following structure:

```
investigation_project_name/
├── config.json          # Project configuration
├── README.md           # Project documentation
├── data/               # Raw data collected during investigation
├── docs/               # Documentation and notes
├── logs/               # Investigation logs and audit trails
└── outputs/            # Final reports and outputs
```

## Development

The system has been enhanced with:

- Proper logging to project-specific directories
- Asynchronous operations for efficient processing
- Comprehensive error handling and state management
- Clean, maintainable codebase with reduced redundancy

## Requirements

- Python 3.8+
- See `requirements.txt` for Python dependencies
- See `frontend/package.json` for frontend dependencies

## Investigation Process

The OSINT-OS system follows a structured approach:
1. **Initialization**: Set up project structure and logging
2. **Task Planning**: Generate investigation plan based on user request
3. **Execution**: Execute tasks while monitoring progress
4. **Output Generation**: Create structured reports in requested format
5. **Cleanup**: Finalize logs and save state

## Contributing

This is an open-source project. Contributions are welcome in the form of bug reports, feature requests, and code contributions.

## License

See the LICENSE file for licensing information.