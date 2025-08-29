import click
from pathlib import Path
from pycodeadvisor.syntax_analyzer import SyntaxAnalyzer
from pycodeadvisor.config import Config
from pycodeadvisor.ai_worker import AIWorker


@click.group()
def main():
    """PyCodeAdvisor - AI-powered Python code analysis"""
    pass


@main.command()
@click.option('--path', default='.', help='Path to analyze (default: current directory)')
@click.option('--no-ai', is_flag=True, help='Skip AI analysis, show syntax errors only')
@click.option('--provider', help='Override default AI provider (openai, anthropic, google)')
@click.option('--max-errors', default=10, help='Maximum number of errors to analyze with AI')
def check(path, no_ai, provider, max_errors):
    """Analyze Python files for potential issues"""
    try:
        # Run syntax analysis
        analyzer = SyntaxAnalyzer(path)
        errors = analyzer.analyze_project()
        
        if not errors:
            click.echo("✓ No syntax errors found!")
            return
        
        # Group errors by file
        errors_by_file = {}
        for error in errors:
            file_path = str(error.file_path)
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        click.echo(f"\nFound {len(errors)} syntax errors in {len(errors_by_file)} files")
        
        # Initialize AI worker if needed
        ai_worker = None
        if not no_ai:
            try:
                config = Config()
                configured_providers = config.list_configured_providers()
                if not configured_providers:
                    click.echo("\nNo API keys configured. Run 'pycodeadvisor setup --env' to configure AI providers.")
                    no_ai = True
                else:
                    provider_to_use = provider or config.config_data.get('default_provider')
                    if provider_to_use not in configured_providers:
                        provider_to_use = configured_providers[0]
                    
                    provider_config = config.get_provider_config(provider_to_use)
                    ai_worker = AIWorker(provider_config)
                    click.echo(f"Using AI provider: {provider_to_use}")
                    
            except Exception as e:
                click.echo(f"AI setup failed: {e}")
                no_ai = True
        
        # Display results grouped by file
        for file_path, file_errors in errors_by_file.items():
            file_name = Path(file_path).name
            click.echo(f"\n{file_name} ({len(file_errors)} errors)")
            click.echo("─" * 40)
            
            # Limit errors per file for AI analysis
            errors_to_analyze = file_errors[:max_errors]
            if len(file_errors) > max_errors:
                click.echo(f"Note: Showing first {max_errors} of {len(file_errors)} errors")
            
            for i, error in enumerate(errors_to_analyze, 1):
                click.echo(f"\nError {i}: {error.error_type} at line {error.line_number}")
                click.echo(f"Message: {error.message}")
                
                if error.code_context:
                    # Show just the error line with context
                    context = error.get_context_snippet()
                    # Extract just the highlighted line for brevity
                    context_lines = context.split('\n')
                    error_line = next((line for line in context_lines if line.startswith('>>>')), "")
                    if error_line:
                        click.echo(f"Code: {error_line}")
                
                # AI analysis for this error
                if not no_ai and ai_worker:
                    try:
                        recommendation = ai_worker.analyze_error(error)
                        
                        # Clean up explanation and fix text
                        explanation = recommendation.explanation.strip()
                        suggested_fix = recommendation.suggested_fix.strip()
                        
                        click.echo(f"Explanation: {explanation}")
                        click.echo(f"Fix: {suggested_fix}")
                        
                        # Show confidence with color
                        confidence_color = "green" if recommendation.is_high_confidence() else "yellow"
                        click.echo(click.style(f"Confidence: {recommendation.confidence_score:.0%}", fg=confidence_color))
                        
                    except Exception as ai_error:
                        click.echo(f"AI analysis failed: {ai_error}")
                
                if i < len(errors_to_analyze):
                    click.echo()  # Empty line between errors
        
        click.echo(f"\n{'='*50}")
        click.echo("Analysis complete")
        
    except ValueError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Unexpected error: {e}")


@main.command()
def config():
    """Show current configuration"""
    try:
        config_obj = Config()
        click.echo(str(config_obj))
        
        # Show available providers
        configured = config_obj.list_configured_providers()
        click.echo(f"\nProvider Status:")
        
        providers = ['openai', 'anthropic', 'google']
        for provider in providers:
            status = "✓ Configured" if provider in configured else "✗ Not configured"
            color = "green" if provider in configured else "red"
            click.echo(f"  {provider}: {click.style(status, fg=color)}")
        
        # Check for .env file
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            click.echo(f"\n.env file: {env_file} (found)")
        else:
            click.echo(f"\n.env file: Not found")
            
    except Exception as e:
        click.echo(f"Error reading configuration: {e}")


@main.command()
@click.option('--env', is_flag=True, help='Use .env file instead of YAML config')
def setup(env):
    """Interactive setup for API keys"""
    try:
        config_obj = Config()
        click.echo("PyCodeAdvisor Setup")
        click.echo("=" * 20)
        
        if env:
            # Handle .env file setup
            env_file = Path.cwd() / ".env"
            
            if not env_file.exists():
                click.echo("Creating .env file for API keys...")
                config_obj.create_dotenv_template()
                click.echo(f"Created .env template: {env_file}")
            
            click.echo(f"\nConfiguration will be saved to: {env_file}")
            click.echo("Configure API keys (press Enter to skip):")
            
            # Read current .env values
            current_keys = {}
            if env_file.exists():
                with env_file.open('r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if not value.startswith('your-'):
                                current_keys[key] = value
            
            # Update .env file with user input
            new_env_lines = ["# PyCodeAdvisor API Keys\n"]
            
            providers = {
                'GOOGLE_API_KEY': 'Google Gemini API Key',
                'OPENAI_API_KEY': 'OpenAI API Key (optional)',
                'ANTHROPIC_API_KEY': 'Anthropic Claude API Key (optional)'
            }
            
            for key, description in providers.items():
                current = current_keys.get(key, '')
                status = "✓ Configured" if current else "✗ Not configured"
                
                click.echo(f"\n{description} ({status}):")
                new_key = click.prompt(f"  Enter {key}", default=current, show_default=False)
                
                if new_key.strip():
                    new_env_lines.append(f"{key}={new_key.strip()}\n")
                else:
                    new_env_lines.append(f"{key}=your-key-here\n")
            
            # Write updated .env file
            with env_file.open('w') as f:
                f.writelines(new_env_lines)
            
            click.echo(f"\n✓ .env file updated: {env_file}")
            click.echo("Your API keys are stored locally and will not be committed to git.")
            
            # Add .env to .gitignore if it doesn't exist
            gitignore = Path.cwd() / ".gitignore"
            gitignore_content = ""
            if gitignore.exists():
                gitignore_content = gitignore.read_text()
            
            if ".env" not in gitignore_content:
                with gitignore.open('a') as f:
                    f.write("\n# API keys\n.env\n")
                click.echo("Added .env to .gitignore for security.")
            
        else:
            # Original YAML setup
            config_file = config_obj.get_config_file_path()
            if not config_file:
                click.echo("No configuration file found. Creating default configuration...")
                config_file = config_obj.create_config_file()
                click.echo(f"Created config file: {config_file}")
            
            click.echo(f"\nConfiguration file: {config_file}")
            click.echo("\nConfigure AI providers (press Enter to skip):")
            
            # Setup each provider
            providers = {
                'openai': 'OpenAI API Key (starts with sk-)',
                'anthropic': 'Anthropic API Key (starts with sk-ant-)',
                'google': 'Google API Key (starts with AIza)'
            }
            
            for provider, description in providers.items():
                current_key = config_obj.config_data.get('providers', {}).get(provider, {}).get('api_key')
                status = "✓ Configured" if current_key else "✗ Not configured"
                
                click.echo(f"\n{provider.title()} ({status}):")
                api_key = click.prompt(f"  {description}", default="", show_default=False)
                
                if api_key.strip():
                    config_obj.set_provider_config(provider, api_key.strip())
                    click.echo(f"  ✓ {provider.title()} API key saved")
            
            # Set default provider
            configured_providers = config_obj.list_configured_providers()
            if configured_providers:
                if len(configured_providers) == 1:
                    default_provider = configured_providers[0]
                    config_obj.config_data['default_provider'] = default_provider
                    config_obj._save_config()
                    click.echo(f"\nDefault provider set to: {default_provider}")
                else:
                    click.echo(f"\nConfigured providers: {', '.join(configured_providers)}")
                    default = click.prompt("Choose default provider", 
                                         type=click.Choice(configured_providers),
                                         default=configured_providers[0])
                    config_obj.config_data['default_provider'] = default
                    config_obj._save_config()
                    click.echo(f"Default provider set to: {default}")
        
        click.echo(f"\n✓ Setup complete!")
        click.echo("You can now run 'pycodeadvisor check' to analyze your code.")
        
    except Exception as e:
        click.echo(f"Setup failed: {e}")


@main.command()
@click.argument('provider', type=click.Choice(['openai', 'anthropic', 'google']))
def test_provider(provider):
    """Test if a provider is working correctly"""
    try:
        config_obj = Config()
        provider_config = config_obj.get_provider_config(provider)
        
        click.echo(f"Testing {provider} connection...")
        
        # Create a simple test error event
        from pycodeadvisor.models import ErrorEvent
        test_error = ErrorEvent(
            file_path="test.py",
            line_number=1,
            error_type="SyntaxError",
            message="invalid syntax",
            code_context=["print('hello world'"],
            context_start_line=1
        )
        
        ai_worker = AIWorker(provider_config)
        recommendation = ai_worker.analyze_error(test_error)
        
        click.echo(f"✓ {provider} is working!")
        click.echo(f"Model: {ai_worker.get_provider_info()['model']}")
        click.echo(f"Test recommendation confidence: {recommendation.confidence_score:.1%}")
        
    except ValueError as e:
        click.echo(f"✗ Configuration error: {e}")
    except Exception as e:
        click.echo(f"✗ {provider} test failed: {e}")


if __name__ == "__main__":
    main()