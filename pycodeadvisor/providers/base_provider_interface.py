from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    def generate_recommendation(self, prompt: str) -> str:
        """Generate AI response from prompt"""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return maximum tokens for this provider"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return model name/identifier"""
        pass