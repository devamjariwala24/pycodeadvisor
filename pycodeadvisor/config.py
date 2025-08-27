import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile


class Config:
    """Configuration management for PyCodeAdvisor"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Optional path to config file. If None, uses default locations.
        """
        self.config_data = {}
        self.config_file = None
        
        # Try to load configuration from various sources
        self._load_config(config_path)
    
    def _get_default_config_paths(self) -> List[Path]:
        """Get list of default configuration file locations in order of preference"""
        paths = []
        
        # 1. Current directory
        paths.append(Path.cwd() / "pycodeadvisor.yaml")
        
        # 2. User home directory
        home_path = Path.home() / ".pycodeadvisor" / "config.yaml"
        paths.append(home_path)
        
        # 3. User config directory (cross-platform)
        if os.name == 'posix':  # Unix-like systems (Linux, macOS)
            config_dir = Path.home() / ".config" / "pycodeadvisor"
        elif os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', str(Path.home()))) / "pycodeadvisor"
        else:  # Other systems
            config_dir = Path.home() / ".pycodeadvisor"
        
        paths.append(config_dir / "config.yaml")
        
        return paths
    
    def _load_config(self, custom_path: Optional[str] = None):
        """Load configuration from file and environment variables"""
        config_loaded = False
        
        if custom_path:
            # Try custom path first
            config_file = Path(custom_path)
            if config_file.exists():
                self.config_data = self._load_yaml_file(config_file)
                self.config_file = config_file
                config_loaded = True
        
        if not config_loaded:
            # Try default locations
            for config_path in self._get_default_config_paths():
                if config_path.exists():
                    self.config_data = self._load_yaml_file(config_path)
                    self.config_file = config_path
                    config_loaded = True
                    break
        
        if not config_loaded:
            # Initialize with empty config
            self.config_data = self._get_default_config()
        
        # Override with environment variables
        self._load_environment_variables()
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Cannot read configuration file {file_path}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            'providers': {
                'openai': {
                    'api_key': None,
                    'model': 'gpt-3.5-turbo'
                },
                'anthropic': {
                    'api_key': None,
                    'model': 'claude-3-haiku-20240307'
                },
                'google': {
                    'api_key': None,
                    'model': 'gemini-1.5-flash'
                }
            },
            'default_provider': 'openai',
            'analysis': {
                'max_files': 100,
                'excluded_dirs': ['.git', '__pycache__', 'venv', '.pytest_cache', 'node_modules']
            }
        }
    
    def _load_environment_variables(self):
        """Override configuration with environment variables"""
        # Provider API keys
        env_mappings = {
            'OPENAI_API_KEY': ['providers', 'openai', 'api_key'],
            'ANTHROPIC_API_KEY': ['providers', 'anthropic', 'api_key'],
            'GOOGLE_API_KEY': ['providers', 'google', 'api_key'],
            'PYCODEADVISOR_PROVIDER': ['default_provider']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value:
                self._set_nested_config(config_path, env_value)
    
    def _set_nested_config(self, path: List[str], value: Any):
        """Set nested configuration value"""
        current = self.config_data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get_provider_config(self, provider_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get provider configuration for AIWorker
        
        Args:
            provider_type: Specific provider type. If None, uses default provider.
            
        Returns:
            Dictionary with type, api_key, and model
        """
        if provider_type is None:
            provider_type = self.config_data.get('default_provider', 'openai')
        
        providers = self.config_data.get('providers', {})
        provider_config = providers.get(provider_type, {})
        
        if not provider_config.get('api_key'):
            raise ValueError(f"No API key configured for provider '{provider_type}'. "
                           f"Set it in config file or environment variable.")
        
        return {
            'type': provider_type,
            'api_key': provider_config['api_key'],
            'model': provider_config.get('model')
        }
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration for SyntaxAnalyzer"""
        return self.config_data.get('analysis', {
            'max_files': 100,
            'excluded_dirs': ['.git', '__pycache__', 'venv']
        })
    
    def validate_config(self, provider_type: Optional[str] = None) -> bool:
        """
        Validate configuration
        
        Args:
            provider_type: Provider to validate. If None, validates default provider.
            
        Returns:
            True if configuration is valid
        """
        try:
            provider_config = self.get_provider_config(provider_type)
            
            # Check required fields
            if not provider_config.get('api_key'):
                return False
            
            if not provider_config.get('type'):
                return False
            
            return True
            
        except (ValueError, KeyError):
            return False
    
    def list_configured_providers(self) -> List[str]:
        """Get list of providers with API keys configured"""
        configured = []
        providers = self.config_data.get('providers', {})
        
        for provider_type, config in providers.items():
            if config.get('api_key'):
                configured.append(provider_type)
        
        return configured
    
    def create_config_file(self, config_path: Optional[Path] = None) -> Path:
        """
        Create a configuration file with default structure
        
        Args:
            config_path: Path for new config file. If None, uses default location.
            
        Returns:
            Path to created configuration file
        """
        if config_path is None:
            # Use first default path (current directory)
            config_path = self._get_default_config_paths()[0]
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create configuration file
        default_config = self._get_default_config()
        
        with config_path.open('w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return config_path
    
    def set_provider_config(self, provider_type: str, api_key: str, model: Optional[str] = None):
        """
        Set provider configuration and save to file
        
        Args:
            provider_type: Provider type (openai, anthropic, google)
            api_key: API key for the provider
            model: Optional model name
        """
        if 'providers' not in self.config_data:
            self.config_data['providers'] = {}
        
        if provider_type not in self.config_data['providers']:
            self.config_data['providers'][provider_type] = {}
        
        self.config_data['providers'][provider_type]['api_key'] = api_key
        
        if model:
            self.config_data['providers'][provider_type]['model'] = model
        
        self._save_config()
    
    def _save_config(self):
        """Save current configuration to file"""
        if self.config_file is None:
            self.config_file = self.create_config_file()
        
        with self.config_file.open('w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
    
    def get_config_file_path(self) -> Optional[Path]:
        """Get path to current configuration file"""
        return self.config_file
    
    def __str__(self) -> str:
        """String representation of configuration"""
        configured_providers = self.list_configured_providers()
        default_provider = self.config_data.get('default_provider', 'openai')
        
        return f"""PyCodeAdvisor Configuration:
  Config file: {self.config_file or 'Not found'}
  Default provider: {default_provider}
  Configured providers: {', '.join(configured_providers) or 'None'}
  Analysis max files: {self.get_analysis_config().get('max_files', 'Not set')}"""