from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

class ErrorEvent:
    """Represents a detected error in Python code"""
    
    def __init__(self, file_path: str, line_number: int, error_type: str, message: str,
                 code_context: Optional[List[str]] = None, 
                 context_start_line: Optional[int] = None,
                 stack_trace: Optional[str] = None, 
                 local_variables: Optional[Dict] = None):
        """
        Initialize an ErrorEvent
        
        Args:
            file_path: Path to the file where error occurred
            line_number: Line number of the error in the actual file
            error_type: Type of error (SyntaxError, NameError, etc.)
            message: Error message
            code_context: Lines of code around the error
            context_start_line: What line number does code_context[0] represent
            stack_trace: Full stack trace (None for static analysis)
            local_variables: Local variables at error point (None for static analysis)
        """
        self.file_path = Path(file_path)
        self.line_number = line_number
        self.error_type = error_type
        self.message = message
        self.code_context = code_context or []
        self.context_start_line = context_start_line
        self.stack_trace = stack_trace
        self.local_variables = local_variables or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorEvent to dictionary for serialization"""
        return {
            'file_path': str(self.file_path),
            'line_number': self.line_number,
            'error_type': self.error_type,
            'message': self.message,
            'code_context': self.code_context,
            'context_start_line': self.context_start_line,
            'stack_trace': self.stack_trace,
            'local_variables': self.local_variables,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorEvent':
        """Create ErrorEvent from dictionary"""
        # Step 1: Extract required fields
        file_path = data['file_path']
        line_number = data['line_number']
        error_type = data['error_type']
        message = data['message']
        
        # Step 2: Extract optional fields with defaults
        code_context = data.get('code_context', None)
        context_start_line = data.get('context_start_line', None)
        stack_trace = data.get('stack_trace', None)
        local_variables = data.get('local_variables', None)
        
        # Step 3: Create the instance
        cls_object = cls(
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            message=message,
            code_context=code_context,
            context_start_line=context_start_line,
            stack_trace=stack_trace,
            local_variables=local_variables
        )
        
        # Step 4: Handle timestamp conversion
        if 'timestamp' in data:
            cls_object.timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls_object
    
    def get_context_snippet(self, lines_before: int = 3, lines_after: int = 3) -> str:
        """Get formatted code context around the error"""
        # Check if we have context
        if not self.code_context or self.context_start_line is None:
            return "No code context available"
        
        # Calculate error position in our context list
        error_index = self.line_number - self.context_start_line
        
        # Validate error_index is within our context
        if error_index < 0 or error_index >= len(self.code_context):
            return "Error line not found in context"
        
        # Calculate range to display
        start_index = max(0, error_index - lines_before)
        end_index = min(len(self.code_context), error_index + lines_after + 1)
        
        # Format lines with line numbers
        formatted_lines = []
        for i in range(start_index, end_index):
            actual_line_number = self.context_start_line + i
            code_line = self.code_context[i]
            
            # Highlight the error line
            if i == error_index:
                formatted_lines.append(f">>> {actual_line_number:3}: {code_line}")
            else:
                formatted_lines.append(f"    {actual_line_number:3}: {code_line}")
        
        return "\n".join(formatted_lines)
    
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error (has stack trace) vs static analysis"""
        # TODO: Implement this method
        # Hint: Return True if stack_trace is not None

        return self.stack_trace is not None
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"{self.file_path}:{self.line_number}: {self.error_type} - {self.message}"


class Recommendation:
    """Represents an AI-generated recommendation for fixing an error"""
    
    def __init__(self, error_event: ErrorEvent, explanation: str, suggested_fix: str,
                 confidence_score: float, references: List[str]):
        """
        Initialize a Recommendation
        
        Args:
            error_event: The original error this recommendation addresses
            explanation: AI-generated explanation of the error
            suggested_fix: Specific steps to fix the error
            confidence_score: AI confidence in the recommendation (0.0 - 1.0)
            references: List of documentation links or resources
        """
        self.error_event = error_event
        self.explanation = explanation
        self.suggested_fix = suggested_fix
        self.confidence_score = confidence_score
        self.references = references
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Recommendation to dictionary"""
        # TODO: Implement this method
        # Hint: Include error_event.to_dict() and all recommendation fields

        result = {}
        result['error_event'] = self.error_event.to_dict()
        result['explanation'] = self.explanation
        result['suggested_fix'] = self.suggested_fix
        result['confidence_score'] = self.confidence_score
        result['references'] = self.references
        result['created_at'] = self.created_at.isoformat()

        return result
    
    def format_for_terminal(self) -> str:
        """Format recommendation for terminal output with colors"""
        return f"""
        ERROR: {self.error_event.file_path}:{self.error_event.line_number}
        Type: {self.error_event.error_type}
        Message: {self.error_event.message}

        EXPLANATION: {self.explanation}

        SUGGESTED FIX: {self.suggested_fix}

        Confidence: {self.confidence_score:.1%}
        """
    
    def is_high_confidence(self) -> bool:
        """Check if recommendation has high confidence (>0.7)"""
        # TODO: Implement this method
        # Hint: Return True if confidence_score > 0.7
        return self.confidence_score > 0.7
    
    def __str__(self) -> str:
        return f"Recommendation for {self.error_event.file_path}:{self.error_event.line_number}"


class RecommendationBuilder:
    """Builder pattern for constructing Recommendation objects step by step"""
    
    def __init__(self):
        """Initialize empty builder"""
        self._error_event: Optional[ErrorEvent] = None
        self._explanation: Optional[str] = None
        self._suggested_fix: Optional[str] = None
        self._confidence_score: Optional[float] = None
        self._references: List[str] = []
    
    def set_error_event(self, error_event: ErrorEvent) -> 'RecommendationBuilder':
        """Set the error event this recommendation addresses"""
        self._error_event = error_event
        return self
    
    def set_explanation(self, explanation: str) -> 'RecommendationBuilder':
        """Set the explanation of why the error occurred"""
        # TODO: Implement this method
        # Hint: Store explanation and return self for chaining
        self._explanation = explanation
        return self
    
    def set_suggested_fix(self, suggested_fix: str) -> 'RecommendationBuilder':
        """Set the suggested fix for the error"""
        # TODO: Implement this method
        # Hint: Store suggested_fix and return self for chaining
        self._suggested_fix = suggested_fix
        return self
    
    def set_confidence_score(self, score: float) -> 'RecommendationBuilder':
        """Set confidence score (0.0 - 1.0)"""
        self._confidence_score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
        return self
    
    def add_reference(self, reference: str) -> 'RecommendationBuilder':
        """Add a documentation reference or helpful link"""
        # TODO: Implement this method
        # Hint: Append to _references list and return self
        self._references.append(reference)
        return self
    
    def build(self) -> Recommendation:
        """Build the final Recommendation object"""
        # TODO: Implement this method with validation
        # Hint: Check required fields are set, raise ValueError if not, create Recommendation
        if self._error_event is None:
            raise ValueError("ErrorEvent is required - call set_error_event() first")
        if self._explanation is None:
            raise ValueError("Explanation is required - call set_explanation() first")
        if self._suggested_fix is None:
            raise ValueError("Suggested Fix is required - call set_suggested_fix() first")
        if self._confidence_score is None:
            raise ValueError("Confidence Score is required - call set_confidence_score() first")
        
        recommendation = Recommendation(self._error_event, self._explanation, self._suggested_fix, self._confidence_score, self._references)
        return recommendation
    
    def reset(self) -> 'RecommendationBuilder':
        """Reset builder to initial state for reuse"""
        self._error_event = None
        self._explanation = None
        self._suggested_fix = None
        self._confidence_score = None
        self._references = []
        return self