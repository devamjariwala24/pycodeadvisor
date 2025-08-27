from typing import Dict, Any
from pycodeadvisor.models import ErrorEvent, Recommendation, RecommendationBuilder
from pycodeadvisor.providers import OpenAIProvider, AnthropicProvider, GoogleProvider


class AIWorker:
    """Main AI analysis worker with multi-provider support"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        """
        Initialize AIWorker with provider configuration
        
        Args:
            provider_config: Dictionary with 'type', 'api_key', and optional 'model'
                Example: {'type': 'openai', 'api_key': 'sk-...', 'model': 'gpt-4'}
        """
        self.provider = self._create_provider(provider_config)
    
    def _create_provider(self, config: Dict[str, Any]):
        """Factory method to create appropriate provider"""
        provider_type = config.get('type', '').lower()
        api_key = config.get('api_key')
        model = config.get('model')
        
        if not api_key:
            raise ValueError("API key is required")
        
        if provider_type == "openai":
            return OpenAIProvider(api_key, model) if model else OpenAIProvider(api_key)
        elif provider_type == "anthropic":
            return AnthropicProvider(api_key, model) if model else AnthropicProvider(api_key)
        elif provider_type == "google":
            return GoogleProvider(api_key, model) if model else GoogleProvider(api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider_type}. Supported: openai, anthropic, google")
    
    def analyze_error(self, error_event: ErrorEvent) -> Recommendation:
        """
        Analyze an error and generate AI-powered recommendation
        
        Args:
            error_event: ErrorEvent from syntax analysis
            
        Returns:
            Recommendation object with AI-generated advice
        """
        # Build prompt from error context
        prompt = self._build_prompt(error_event)
        
        # Get AI response
        ai_response = self.provider.generate_recommendation(prompt)
        
        # Parse response into structured data
        parsed_response = self._parse_ai_response(ai_response)
        
        # Build recommendation using RecommendationBuilder
        builder = RecommendationBuilder()
        recommendation = (builder
            .set_error_event(error_event)
            .set_explanation(parsed_response['explanation'])
            .set_suggested_fix(parsed_response['suggested_fix'])
            .set_confidence_score(parsed_response['confidence'])
            .build())
        
        return recommendation
    
    def _build_prompt(self, error_event: ErrorEvent) -> str:
        """Create structured prompt for AI analysis"""
        context_snippet = error_event.get_context_snippet()
        
        prompt = f"""Analyze this Python error and provide a helpful recommendation:

        FILE: {error_event.file_path}
        ERROR TYPE: {error_event.error_type}
        ERROR MESSAGE: {error_event.message}
        LINE: {error_event.line_number}

        CODE CONTEXT:
        {context_snippet}

        Please provide your response in this exact format:

        EXPLANATION:
        [Explain what caused this error in simple terms]

        SUGGESTED FIX:
        [Provide specific steps to fix the error]

        CONFIDENCE:
        [Rate your confidence from 0.0 to 1.0]"""
        
        return prompt
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Extract structured information from AI response"""
        lines = response.strip().split('\n')
        
        explanation = ""
        suggested_fix = ""
        confidence = 0.5  # default
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("EXPLANATION:"):
                current_section = "explanation"
                continue
            elif line.startswith("SUGGESTED FIX:"):
                current_section = "suggested_fix"
                continue
            elif line.startswith("CONFIDENCE:"):
                current_section = "confidence"
                # Extract confidence value
                try:
                    confidence_text = line.replace("CONFIDENCE:", "").strip()
                    confidence = float(confidence_text)
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range
                except (ValueError, IndexError):
                    confidence = 0.5
                continue
            
            # Add content to current section
            if current_section == "explanation" and line:
                explanation += line + " "
            elif current_section == "suggested_fix" and line:
                suggested_fix += line + " "
        
        return {
            'explanation': explanation.strip() or "Unable to analyze this error",
            'suggested_fix': suggested_fix.strip() or "No specific fix suggested",
            'confidence': confidence
        }
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about current provider"""
        return {
            'model': self.provider.get_model_name(),
            'max_tokens': str(self.provider.get_max_tokens()),
            'type': type(self.provider).__name__
        }