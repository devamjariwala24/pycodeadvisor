import requests
from pycodeadvisor.providers.base_provider_interface import BaseProvider


class GoogleProvider(BaseProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key)
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    def generate_recommendation(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add system instruction to the prompt for Google
        enhanced_prompt = f"""You are a Python code analysis expert. Provide clear, actionable advice for fixing code errors.

{prompt}"""
        
        data = {
            "contents": [{
                "parts": [{"text": enhanced_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}", 
                headers=headers, 
                json=data, 
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            return response_data['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Google API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid Google response format: {str(e)}")
    
    def get_max_tokens(self) -> int:
        return 1000000
    
    def get_model_name(self) -> str:
        return self.model