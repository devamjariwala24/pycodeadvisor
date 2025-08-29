import ast
from pathlib import Path
from typing import List, Optional, Any

from pycodeadvisor.models import ErrorEvent


class SyntaxAnalyzer:

    def __init__(self, project_path: str, excluded_dirs: Optional[List[str]] = None):

        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not self.project_path.is_dir():
            raise ValueError(f"Project path must be a directory, not a file: {project_path}")
        
        # Step 4: Set up excluded directories with sensible defaults
        self.excluded_dirs = excluded_dirs or ['.git', '__pycache__', 'venv', '.pytest_cache', 'node_modules']

    def should_ignore_directory(self, dir_path: Path) -> bool:
        """Check if directory should be excluded from analysis"""

        if dir_path.name in self.excluded_dirs:
            return True
        
        # Check all parent directories
        for parent in dir_path.parents:
            if parent.name in self.excluded_dirs:
                return True
        
        return False

    def find_python_files(self) -> List[Path]:
        """Discover all Python files in the project directory"""
        python_files = []
        
        try:
            for file_path in self.project_path.rglob("*.py"):
                # Check if file is in an excluded directory
                if self.should_ignore_directory(file_path.parent):
                    continue
                    
                # Add file-level validation
                if self._is_readable_python_file(file_path):
                    python_files.append(file_path)
                    
        except PermissionError as e:
            print(f"Warning: Cannot access some directories due to permissions: {e}")
        
        return python_files

    def _is_readable_python_file(self, file_path: Path) -> bool:
        """Check if file is readable and appears to be a valid Python file"""
        try:
            if not file_path.is_file():
                return False
                
            with file_path.open('r', encoding='utf-8') as f:
                # Try to read first few bytes to ensure it's not binary
                f.read(100)
                
            return True
            
        except (PermissionError, UnicodeDecodeError, OSError):
            return False
        
    def analyze_file(self, file_path: Path) -> List[ErrorEvent]:
        """Parse single file and return any errors found"""
        errors = []
        
        try:
            # Read file content
            with file_path.open('r', encoding='utf-8') as f:
                file_content = f.read()
                lines = file_content.splitlines()
                
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            error = ErrorEvent(
                file_path=str(file_path),
                line_number=1,
                error_type="FileReadError",
                message=f"Cannot read file: {str(e)}"
            )
            return [error]
        
        try:
            # Try AST parsing first
            ast.parse(file_content, filename=str(file_path))
            return []  # No syntax errors found
            
        except SyntaxError:
            # AST parsing failed, use pattern-based detection
            errors = self._detect_multiple_errors(file_path, lines)
            
        return errors

    def _detect_multiple_errors(self, file_path: Path, lines: List[str]) -> List[ErrorEvent]:
        """Detect multiple errors using pattern matching"""
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check for missing colons
            if (line.startswith(('def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally')) 
                and not line.endswith(':')):
                error = self._create_pattern_error(file_path, line_num, "SyntaxError", 
                                                "expected ':'", lines, line_num-1)
                errors.append(error)
            
            # Check for unclosed parentheses/brackets
            if '(' in line and line.count('(') > line.count(')'):
                error = self._create_pattern_error(file_path, line_num, "SyntaxError", 
                                                "'(' was never closed", lines, line_num-1)
                errors.append(error)
            
            if '[' in line and line.count('[') > line.count(']'):
                error = self._create_pattern_error(file_path, line_num, "SyntaxError", 
                                                "'[' was never closed", lines, line_num-1)
                errors.append(error)
            
            # Check for unclosed quotes
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\\"')
            
            if single_quotes % 2 != 0:
                error = self._create_pattern_error(file_path, line_num, "SyntaxError", 
                                                "unterminated string literal", lines, line_num-1)
                errors.append(error)
        
        return errors

    def _create_pattern_error(self, file_path: Path, line_number: int, error_type: str, 
                            message: str, all_lines: List[str], error_index: int) -> ErrorEvent:
        """Create ErrorEvent with context for pattern-detected errors"""
        context_lines = 3
        start_line = max(0, error_index - context_lines)
        end_line = min(len(all_lines), error_index + context_lines + 1)
        
        context = all_lines[start_line:end_line]
        context_start_line = start_line + 1
        
        return ErrorEvent(
            file_path=str(file_path),
            line_number=line_number,
            error_type=error_type,
            message=message,
            code_context=context,
            context_start_line=context_start_line
        )
        
    def extract_code_context(self, file_path: Path, error_line: int, lines_before: int = 3, lines_after: int = 3) -> tuple:
        """Read file and extract lines around the error"""
        try:
            with file_path.open('r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            # Calculate context range
            start_line = max(1, error_line - lines_before)
            end_line = min(len(all_lines), error_line + lines_after)
            
            # Extract context (convert to 0-based indexing)
            context = [line.rstrip('\n') for line in all_lines[start_line-1:end_line]]
            
            return context, start_line
            
        except (UnicodeDecodeError, OSError):
            return [], error_line
        
    def analyze_project(self) -> List[ErrorEvent]:
        """Analyze entire project and return all errors"""
        all_errors = []
        
        # Find all Python files
        python_files = self.find_python_files()
        
        if not python_files:
            print(f"No Python files found in {self.project_path}")
            return all_errors
        
        print(f"Analyzing {len(python_files)} Python files...")
        
        # Analyze each file
        for file_path in python_files:
            try:
                file_errors = self.analyze_file(file_path)
                all_errors.extend(file_errors)
                
            except Exception as e:
                # Create error event for unexpected analysis failures
                error = ErrorEvent(
                    file_path=str(file_path),
                    line_number=1,
                    error_type="AnalysisError",
                    message=f"Unexpected error during analysis: {str(e)}"
                )
                all_errors.append(error)
        
        print(f"Analysis complete. Found {len(all_errors)} errors.")
        return all_errors