import click
from pathlib import Path
from pycodeadvisor.syntax_analyzer import SyntaxAnalyzer

@click.group()
def main():
    """PyCodeAdvisor - AI-powered Python code analysis"""
    pass

@main.command()
@click.option('--path', default='.', help='Path to analyze (default: current directory)')
def check(path):
    """Analyze Python files for potential issues"""
    try:
        analyzer = SyntaxAnalyzer(path)
        errors = analyzer.analyze_project()
        
        if not errors:
            click.echo("No syntax errors found!")
            return
            
        click.echo(f"\nFound {len(errors)} errors:\n")
        for error in errors:
            click.echo(f"{'='*50}")
            click.echo(error.get_context_snippet())
            click.echo()
            
    except ValueError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()