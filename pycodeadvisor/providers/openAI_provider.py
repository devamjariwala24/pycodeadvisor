import requests
from pycodeadvisor.providers.base_provider_interface import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key)
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_recommendation(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a Python code analysis expert. Provide clear, actionable advice for fixing code errors."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid OpenAI response format: {str(e)}")
    
    def get_max_tokens(self) -> int:
        return 4000 if "gpt-3.5" in self.model else 8000
    
    def get_model_name(self) -> str:
        return self.model