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
from dataclasses import dataclass, field


@dataclass
class CodeFeature:
    validation_year: str = None
    imports: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    version_hint: str = "unknown" # Kept for existing logic compat


class CodeAnalyzer:
    """
    Analyzes Python code to estimate its version and dependencies.
    """
    
    # Python 2 specific patterns (extensible rule-based design)
    PY2_PATTERNS = [
        r'print\s+["\']',  # print without parentheses
        r'except\s+\w+\s*,\s*\w+:',  # except Exception, e:
        r'raise\s+\w+\s*,',  # raise Exception, message
        r'exec\s+["\']',  # exec statement (not function)
        r'<>\s*',  # <> operator
        r'`.*`',  # backtick repr
        r'#\s*-\*-\s*coding:\s*utf-8\s*-\*-', # Encoding declaration (common in py2)
    ]
    
    def __init__(self, code_text=None):
        """Initialize the CodeAnalyzer."""
        self.py2_pattern = re.compile('|'.join(self.PY2_PATTERNS))
        # Initial code text if provided (User request style)
        self.code = code_text
        self.tree = None
        if code_text:
            try:
                self.tree = ast.parse(code_text)
            except SyntaxError:
                self.tree = None
    
    def analyze(self, code_text=None) -> CodeFeature:
        """
        Perform analysis returning a structured CodeFeature object.
        Compatible with user Request 2.1.
        """
        # Update internal state if new code provided
        if code_text:
            self.code = code_text
            try:
                self.tree = ast.parse(code_text)
            except SyntaxError:
                self.tree = None
        
        feature = CodeFeature()
        
        if not self.code:
            return feature

        # 1. Validation Year Extraction
        years = re.findall(r'20[1-2][0-9]', self.code)
        if years:
            feature.validation_year = min(years)

        # 2. Version Detection (Legacy Logic Integration)
        feature.version_hint = self.analyze_version(self.code)

        # 3. Import & Keyword Extraction
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        feature.imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        feature.imports.append(node.module.split('.')[0])
                # Specific keyword detection
                elif isinstance(node, ast.Attribute):
                    if node.attr in ['grid_search', 'cross_validation']:
                        feature.keywords.append(f"attr:{node.attr}")
        else:
            # Fallback for Python 2 code that fails AST parsing
            feature.imports = list(self._extract_imports_regex(self.code))
            
        # Deduplicate
        feature.imports = sorted(list(set(feature.imports)))
        
        return feature

    def analyze_version(self, code_text: str) -> str:
        """Analyze code to determine if it's Python 2 or Python 3."""
        if not code_text or not code_text.strip():
            return "unknown"
        
        # Regex-detectable Python 2 patterns
        if self.py2_pattern.search(code_text):
            return "2.7"
        
        # Try parsers
        try:
            ast.parse(code_text)
            if self._has_py3_features(code_text):
                return "3.x"
            return "3.x"
        except SyntaxError as e:
            error_msg = str(e)
            if "Missing parentheses in call to 'print'" in error_msg:
                return "2.7"
            if "invalid syntax" in error_msg and "except" in code_text:
                 if re.search(r'except\s+\w+\s*,\s*\w+:', code_text):
                    return "2.7"
            return "unknown"
        except Exception:
            return "unknown"

    def _has_py3_features(self, code_text: str) -> bool:
        """Check for Python 3 specific features."""
        py3_patterns = [
            r'print\s*\(', r'async\s+def', r'await\s+', 
            r':\s*->\s*', r'@\w+\.setter', r'nonlocal\s+', r'yield\s+from'
        ]
        return bool(re.search('|'.join(py3_patterns), code_text))

    def _extract_imports_regex(self, code_text: str) -> set:
        """Fallback method to extract imports using regex."""
        libraries = set()
        import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        from_pattern = r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        
        for line in code_text.split('\n'):
            match = re.match(import_pattern, line)
            if match:
                libraries.add(match.group(1))
            match_from = re.match(from_pattern, line)
            if match_from:
                libraries.add(match_from.group(1))
        return libraries

    def summary(self, code_text: str) -> Dict[str, any]:
        """Legacy compatibility wrapper for summary dict."""
        feature = self.analyze(code_text)
        return {
            'version': feature.version_hint,
            'libraries': feature.imports,
            'keywords': feature.keywords,
            'validation_year': feature.validation_year,
            'feature_object': feature
        }

# Convenience function kept for compatibility
def analyze_code_file(filepath: str) -> Dict[str, any]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code_text = f.read()
    except Exception as e:
        raise IOError(f"Error reading file {filepath}: {e}")
    analyzer = CodeAnalyzer()
    return analyzer.summary(code_text)
