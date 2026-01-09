"""
Code analyzer for detecting Python version and library dependencies.

This module provides the CodeAnalyzer class which can:
- Detect whether code is Python 2 or Python 3
- Extract imported libraries from code
- Provide a summary of code characteristics
"""

import ast
import re
from typing import List, Dict, Optional


class CodeAnalyzer:
    """
    Analyzes Python code to estimate its version and dependencies.
    
    This class uses AST parsing and pattern matching to determine:
    - Python version (2.x vs 3.x)
    - Imported libraries
    - Potential library version hints (extensible for future rules)
    """
    
    # Known libraries to track (extensible)
    KNOWN_LIBRARIES = {
        'cv2', 'opencv', 'numpy', 'np', 'pandas', 'pd', 
        'sklearn', 'tensorflow', 'tf', 'torch', 'keras',
        'matplotlib', 'scipy', 'PIL', 'requests', 'flask',
        'django', 'fastapi', 'sqlalchemy'
    }
    
    # Python 2 specific patterns (extensible rule-based design)
    PY2_PATTERNS = [
        r'print\s+["\']',  # print without parentheses
        r'except\s+\w+\s*,\s*\w+:',  # except Exception, e:
        r'raise\s+\w+\s*,',  # raise Exception, message
        r'exec\s+["\']',  # exec statement (not function)
        r'<>\s*',  # <> operator
        r'`.*`',  # backtick repr
    ]
    
    def __init__(self):
        """Initialize the CodeAnalyzer."""
        self.py2_pattern = re.compile('|'.join(self.PY2_PATTERNS))
    
    def analyze_version(self, code_text: str) -> str:
        """
        Analyze code to determine if it's Python 2 or Python 3.
        
        Strategy:
        1. Try parsing with Python 3's ast.parse()
        2. If SyntaxError occurs, check error message for Python 2 indicators
        3. Additionally check for Python 2 specific syntax patterns
        
        Args:
            code_text: The Python source code to analyze
            
        Returns:
            Version string: "2.7", "3.x", or "unknown"
        """
        if not code_text or not code_text.strip():
            return "unknown"
        
        # First, check for regex-detectable Python 2 patterns
        if self.py2_pattern.search(code_text):
            return "2.7"
        
        # Try parsing with Python 3 AST
        try:
            ast.parse(code_text)
            # Successfully parsed - likely Python 3
            # But could also be Python 2 code that's compatible
            # Check for Python 3 specific features
            if self._has_py3_features(code_text):
                return "3.x"
            # If no clear Python 3 features, default to 3.x since it parsed
            return "3.x"
            
        except SyntaxError as e:
            # Parse failed - analyze the error
            error_msg = str(e)
            
            # Check for Python 2 specific syntax errors
            # "Missing parentheses in call to 'print'"
            if "Missing parentheses in call to 'print'" in error_msg:
                return "2.7"
            
            # "invalid syntax" with except clause
            if "invalid syntax" in error_msg and "except" in code_text:
                # Check for "except Exception, e:" pattern
                if re.search(r'except\s+\w+\s*,\s*\w+:', code_text):
                    return "2.7"
            
            # Other syntax errors might indicate Python 2
            # Check the line that caused the error
            if hasattr(e, 'text') and e.text:
                if re.search(r'print\s+["\']', e.text):
                    return "2.7"
            
            # Unknown syntax error
            return "unknown"
        
        except Exception:
            # Other parsing errors
            return "unknown"
    
    def _has_py3_features(self, code_text: str) -> bool:
        """
        Check for Python 3 specific features.
        
        Args:
            code_text: The Python source code
            
        Returns:
            True if Python 3 specific features are detected
        """
        # Python 3 specific patterns
        py3_patterns = [
            r'print\s*\(',  # print function
            r'async\s+def',  # async functions
            r'await\s+',  # await keyword
            r':\s*->\s*',  # type annotations with ->
            r'@\w+\.setter',  # property setters (more common in Py3)
            r'nonlocal\s+',  # nonlocal keyword
            r'yield\s+from',  # yield from
        ]
        
        py3_pattern = re.compile('|'.join(py3_patterns))
        return bool(py3_pattern.search(code_text))
    
    def detect_libraries(self, code_text: str) -> List[str]:
        """
        Detect imported libraries in the code.
        
        Scans for ast.Import and ast.ImportFrom nodes to extract library names.
        
        Args:
            code_text: The Python source code to analyze
            
        Returns:
            List of detected library names (deduplicated)
        """
        if not code_text or not code_text.strip():
            return []
        
        libraries = set()
        
        try:
            tree = ast.parse(code_text)
            
            for node in ast.walk(tree):
                # Handle "import module" or "import module as alias"
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        lib_name = alias.name.split('.')[0]  # Get root module
                        libraries.add(lib_name)
                
                # Handle "from module import ..."
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        lib_name = node.module.split('.')[0]  # Get root module
                        libraries.add(lib_name)
        
        except SyntaxError:
            # If AST parsing fails, try regex-based extraction as fallback
            libraries = self._extract_imports_regex(code_text)
        
        except Exception:
            # Other errors - return empty list
            return []
        
        # Filter to only known libraries (optional - can be disabled for full list)
        # For now, return all detected libraries
        return sorted(list(libraries))
    
    def _extract_imports_regex(self, code_text: str) -> set:
        """
        Fallback method to extract imports using regex.
        
        Used when AST parsing fails (e.g., Python 2 code).
        
        Args:
            code_text: The Python source code
            
        Returns:
            Set of library names
        """
        libraries = set()
        
        # Match "import module" or "import module as alias"
        import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        # Match "from module import ..."
        from_pattern = r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        
        for line in code_text.split('\n'):
            # Check for regular import
            match = re.match(import_pattern, line)
            if match:
                libraries.add(match.group(1))
                continue
            
            # Check for from import
            match = re.match(from_pattern, line)
            if match:
                libraries.add(match.group(1))
        
        return libraries
    
    def summary(self, code_text: str) -> Dict[str, any]:
        """
        Generate a comprehensive summary of the code analysis.
        
        Args:
            code_text: The Python source code to analyze
            
        Returns:
            Dictionary containing:
            - version: Estimated Python version ("2.7", "3.x", "unknown")
            - libraries: List of detected imported libraries
            - library_hints: Future extension for library version hints
        """
        version = self.analyze_version(code_text)
        libraries = self.detect_libraries(code_text)
        
        summary_dict = {
            'version': version,
            'libraries': libraries,
            'library_hints': self._get_library_hints(code_text, libraries)
        }
        
        return summary_dict
    
    def _get_library_hints(self, code_text: str, libraries: List[str]) -> Dict[str, Optional[str]]:
        """
        Detect library version hints (extensible rule-based design).
        
        This method provides a framework for future expansion to detect
        specific library versions (e.g., OpenCV 2.x vs 3.x).
        
        Args:
            code_text: The Python source code
            libraries: List of detected libraries
            
        Returns:
            Dictionary mapping library names to version hints
        """
        hints = {}
        
        # OpenCV version detection rules (extensible)
        if 'cv2' in libraries:
            hints['cv2'] = self._detect_opencv_version(code_text)
        
        # Add more library-specific rules here in the future
        # Example:
        # if 'sklearn' in libraries:
        #     hints['sklearn'] = self._detect_sklearn_version(code_text)
        
        return hints
    
    def _detect_opencv_version(self, code_text: str) -> Optional[str]:
        """
        Detect OpenCV version hints from code patterns.
        
        OpenCV 2.x vs 3.x/4.x differences:
        - cv2.cv.CV_* constants (2.x) vs cv2.CV_* (3.x+)
        - Different function signatures
        
        Args:
            code_text: The Python source code
            
        Returns:
            Version hint string or None
        """
        # Check for OpenCV 2.x patterns
        if re.search(r'cv2\.cv\.CV_', code_text):
            return "2.x"
        
        # Check for OpenCV 3.x+ patterns
        if re.search(r'cv2\.CV_', code_text):
            return "3.x+"
        
        # No clear version indicator
        return None


# Convenience function for quick analysis
def analyze_code_file(filepath: str) -> Dict[str, any]:
    """
    Analyze a Python file and return summary.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Analysis summary dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except Exception as e:
        raise IOError(f"Error reading file {filepath}: {e}")
    
    analyzer = CodeAnalyzer()
    return analyzer.summary(code_text)
