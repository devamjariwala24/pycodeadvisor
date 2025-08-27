# PyCodeAdvisor Development Notes

## Project Overview

**Goal**: AI-powered Python debugging assistant that analyzes errors and provides fixes

**Architecture Strategy**: 
- Two development branches: `free-models` vs `premium-models`
- MVP Focus: Static analysis first, then runtime monitoring
- Design Patterns: MVC, Builder, Singleton

## Development Environment Setup

### Virtual Environment
```bash
# Created virtual environment
python3 -m venv pycodeadvisor

# Activation command
source pycodeadvisor/bin/activate

# Location
/Users/DEVAM/Desktop/pycodeadvisor/
```

### Project Structure
```
pycodeadvisor/ (git repo root)
├── README.md
├── pyproject.toml (package configuration)
├── pycodeadvisor/ (Python package)
│   ├── __init__.py
│   ├── cli.py (command-line interface)
│   ├── syntax_analyzer.py (AST-based analysis)
│   └── models.py (data structures)
└── venv/ (virtual environment - renamed from 'pycodeadvisor')
```

## Key Development Commands

```bash
# Virtual environment management
source pycodeadvisor/bin/activate

# Package installation (editable mode)
pip install -e .

# CLI testing
pycodeadvisor --help
pycodeadvisor check
```

## Configuration Files

### pyproject.toml Structure
```toml
[project]
name = "pycodeadvisor"
version = "0.1.0"
dependencies = [
    "click>=8.0.0",      # CLI framework
    "requests>=2.25.0",  # API calls
    "PyYAML>=6.0",       # Configuration
]

[project.scripts]
pycodeadvisor = "pycodeadvisor.cli:main"
```

**Key Dependencies**:
- `click` - Command-line interface framework
- `requests` - HTTP requests for AI API calls
- `PyYAML` - Configuration file handling

## Click CLI Framework Learning

### Basic Structure
```python
import click

@click.group()
def main():
    """PyCodeAdvisor - AI-powered Python code analysis"""
    pass

@main.command()
def check():
    """Analyze Python files for potential issues"""
    click.echo("Static analysis feature - coming soon!")

if __name__ == "__main__":
    main()
```

### Key Click Concepts
- `@click.group()` - Creates main command group that can hold subcommands
- `@main.command()` - Registers subcommands under the main group
- `click.echo()` - Preferred over `print()` for better terminal compatibility
- Docstrings automatically become help text
- `if __name__ == "__main__":` - Allows direct script execution

### Command Structure Created
- `pycodeadvisor --help` - Main help
- `pycodeadvisor check` - Static analysis command
- `pycodeadvisor check --help` - Subcommand help

## Technical Architecture Decisions

### Error Analysis Strategy
1. **Syntax/Indentation Errors**: Use Python AST parsing (immediate detection)
2. **Runtime Errors**: AI-powered analysis with context
3. **Prioritization**: Individual errors first, then error chains
4. **Output**: Terminal-based with file:line format

### AI Integration Approach
- **Free Branch**: Hugging Face models, Ollama + CodeLlama
- **Premium Branch**: OpenAI GPT-3.5/4, Claude API
- **User provides API keys** for premium version
- **Cost management**: Rate limiting, usage tracking

### Performance Considerations
- Manual command execution (no automatic file watching for MVP)
- Limit analysis to reasonable file counts (50-100 max)
- Cache AI responses for identical errors
- Process files in dependency order when possible

## Next Development Steps

### Immediate Tasks
1. **Implement syntax_analyzer.py**:
   - Use `ast.parse()` for syntax error detection
   - Implement file discovery with `pathlib`
   - Skip common directories (`__pycache__`, `.git`, `venv`)

2. **Create models.py**:
   - `ErrorEvent` class (file, line, error_type, message, context)
   - `Recommendation` class (explanation, suggested_fix, confidence)
   - `RecommendationBuilder` pattern implementation

3. **Enhance CLI interface**:
   - Add command line options (`--path`, `--max-files`)
   - Implement proper error handling
   - Add colored output for better readability

### Future Features
- Runtime error monitoring with `sys.excepthook`
- AI model integration (free and premium versions)
- Configuration file support (`config.yaml`)
- Chrome extension/IDE plugin integration

## Common Issues & Solutions

### Virtual Environment Issues
- **Problem**: Created venv with same name as project
- **Solution**: Renamed venv folder to avoid confusion

### Import Errors
- **Problem**: `cannot import name 'main' from 'pycodeadvisor.cli'`
- **Solution**: Ensure CLI functions are properly defined before testing commands

### Package Installation
- **Remember**: Run `pip install -e .` after modifying `pyproject.toml`
- **Check**: Use `pip list` to verify package installation

## Learning Notes

### Design Pattern Applications
- **MVC**: Separate data models, business logic, and user interface
- **Builder**: Complex object construction (RecommendationBuilder)
- **Singleton**: Resource management (database, API clients)

### Development Best Practices
- Start with simple MVP before adding complexity
- Use virtual environments to avoid dependency conflicts
- Test CLI commands frequently during development
- Keep configuration separate from code