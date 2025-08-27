import requests
from pycodeadvisor.providers.base_provider_interface import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key)
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def generate_recommendation(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "system": "You are a Python code analysis expert. Provide clear, actionable advice for fixing code errors."
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            return response_data['content'][0]['text'].strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Anthropic API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid Anthropic response format: {str(e)}")
    
    def get_max_tokens(self) -> int:
        return 100000
    
    def get_model_name(self) -> str:
        return self.model