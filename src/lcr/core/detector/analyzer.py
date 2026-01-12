"""
Code analyzer for detecting Python version and library dependencies.

This module provides the CodeAnalyzer class which can:
- Detect whether code is Python 2 or Python 3
- Extract imported libraries from code
- Provide a summary of code characteristics
"""

import ast
import re
import json
import urllib.request
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path


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
        self.mappings = self._load_mappings()
        
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

    def _load_mappings(self) -> Dict:
        """Load library mappings from JSON file."""
        import json
        from pathlib import Path
        try:
            # Locate mapping file relative to this file
            mapping_path = Path(__file__).parent / "mappings" / "library.json"
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CodeAnalyzer] Warning: Failed to load library mappings: {e}")
        return {}

    def guess_package_name(self, import_name: str) -> tuple[Optional[str], bool]:
        """
        Guess PyPI package name from import name using PyPI JSON API.
        
        Returns:
            (package_name, is_confirmed_on_pypi)
        """
        # 1. Try exact match
        if self._check_pypi(import_name):
            return import_name, True
            
        # 2. Try hyphen/underscore swap
        swapped = import_name.replace('_', '-')
        if swapped != import_name and self._check_pypi(swapped):
            return swapped, True
            
        return import_name, False

    def _check_pypi(self, package_name: str) -> bool:
        """Check if package exists on PyPI via JSON API."""
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                # response.status doesn't exist - use getcode() instead
                return response.getcode() == 200
        except Exception:
            return False

    def resolve_packages(self, imports: List[str]) -> Dict:
        """
        Resolve import names to Pip and Apt packages.
        Returns detailed resolution map:
        {
            "pip": set(),
            "apt": set(),
            "unresolved": set(),
            "reasons": {}
        }
        """
        resolved = {
            "pip": set(),
            "apt": set(),
            "unresolved": set(),
            "reasons": {}
        }
        
        stdlib = {'os', 'sys', 're', 'json', 'math', 'datetime', 'time', 'random', 
                 'collections', 'itertools', 'functools', 'logging', 'pathlib',
                 'typing', 'subprocess', 'ast', 'shutil', 'hashlib', 'csv', 'argparse'}

        for imp in imports:
            # Skip standard library modules
            if imp in stdlib:
                continue
                
            if imp in self.mappings:
                # Mapped locally in library.json
                mapping = self.mappings[imp]
                
                # Pip packages (list)
                pip_pkgs = mapping.get("pip", [])
                if isinstance(pip_pkgs, str): # Legacy/Migration safety
                    pip_pkgs = [pip_pkgs]
                elif pip_pkgs is None: # Explicit None safety
                    pip_pkgs = []
                    
                for pkg in pip_pkgs:
                    resolved["pip"].add(pkg)
                    resolved["reasons"][pkg] = f"Mapped from import '{imp}'"
                
                # Apt packages
                apt_pkgs = mapping.get("apt", [])
                if isinstance(apt_pkgs, str):
                    apt_pkgs = [apt_pkgs]
                elif apt_pkgs is None:
                    apt_pkgs = []
                    
                for pkg in apt_pkgs:
                    resolved["apt"].add(pkg)
                    resolved["reasons"][pkg] = f"System dependency for '{imp}'"
            else:
                # Unknown import - Not in library.json
                # Try to find it on PyPI using guess_package_name
                candidate, confirmed = self.guess_package_name(imp)
                
                if confirmed:
                    # CRITICAL: Package found on PyPI, add to pip set
                    resolved["pip"].add(candidate)
                    resolved["reasons"][candidate] = f"PyPI confirmed package for import '{imp}'"
                    print(f"[CodeAnalyzer] PyPI Match: '{imp}' -> '{candidate}' (confirmed)")
                else:
                    # Not found on PyPI either
                    resolved["unresolved"].add(candidate)
                    resolved["reasons"][candidate] = f"Unconfirmed import '{imp}' (not in library.json, not found on PyPI)"
                    print(f"[CodeAnalyzer] Unresolved: '{imp}' (candidate: '{candidate}')")

        return resolved

    def update_mapping(self, import_name: str, package_config: Dict):
        """
        Update local mapping file with new package info.
        
        Args:
            import_name: The import name (e.g., "cv2")
            package_config: Dict like {"pip": ["opencv-python"], "apt": []}
        """
        try:
           mapping_path = Path(__file__).parent / "mappings" / "library.json"
           
           # Load current
           if mapping_path.exists():
               with open(mapping_path, 'r', encoding='utf-8') as f:
                   data = json.load(f)
           else:
               data = {}
               
           # Update
           data[import_name] = package_config
           
           # Save atomic-ish
           temp_path = mapping_path.with_suffix('.tmp')
           with open(temp_path, 'w', encoding='utf-8') as f:
               json.dump(data, f, indent=4, ensure_ascii=False)
           
           temp_path.replace(mapping_path)
           
           # Update in-memory
           self.mappings[import_name] = package_config
           
        except Exception as e:
            print(f"[CodeAnalyzer] Failed to update mapping: {e}")

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
