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
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Global cache for PyPI results (Session-level persistence)
_PYPI_CACHE = {}

@dataclass
class PyPiPackageInfo:
    """Structure for PyPI lookup results."""
    name: str
    exists: bool
    is_dummy: bool = False
    suggestion: Optional[str] = None
    description: str = ""


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

    def guess_package_name(self, import_name: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Guess PyPI package name from import name using PyPI JSON API.
        
        Returns:
            (package_name, is_confirmed_on_pypi, suggestion)
        """
        # 1. Try exact match
        info = self._check_pypi(import_name)
        if info.exists:
            if info.is_dummy and info.suggestion:
                return import_name, True, info.suggestion
            return import_name, True, None
            
        # 2. Try hyphen/underscore swap
        swapped = import_name.replace('_', '-')
        if swapped != import_name:
            info_swapped = self._check_pypi(swapped)
            if info_swapped.exists:
                if info_swapped.is_dummy and info_swapped.suggestion:
                    return swapped, True, info_swapped.suggestion
                return swapped, True, None
            
        return import_name, False, None

    def _check_pypi(self, package_name: str) -> PyPiPackageInfo:
        """
        Check if package exists on PyPI via JSON API. 
        Uses global cache to prevent redundant requests.
        """
        if package_name in _PYPI_CACHE:
            return _PYPI_CACHE[package_name]

        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            # Enforce strict timeout to prevent UI blocking
            with urllib.request.urlopen(url, timeout=2.0) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    info = data.get('info', {})
                    
                    description = info.get('description', '') or info.get('summary', '')
                    size = 0
                    if data.get('urls'):
                         size = data['urls'][0].get('size', 0)
                    
                    # Dummy Detection Logic
                    is_dummy = False
                    suggestion = None
                    
                    # Heuristic A: Extremely small size (< 2KB)
                    if 0 < size < 2000:
                        is_dummy = True
                        
                    # Heuristic B: Keywords in description
                    lower_desc = description.lower()
                    if "please install" in lower_desc or "use" in lower_desc and "instead" in lower_desc:
                         is_dummy = True
                         
                         # Try to extract suggestion: "Please install X instead"
                         # Simple regex for "install X instead"
                         match = re.search(r'install\s+([a-zA-Z0-9_\-]+)\s+instead', lower_desc)
                         if match:
                             suggestion = match.group(1)

                    result = PyPiPackageInfo(
                        name=package_name,
                        exists=True,
                        is_dummy=is_dummy,
                        suggestion=suggestion,
                        description=info.get('summary', '')
                    )
                    _PYPI_CACHE[package_name] = result
                    return result

        except Exception:
            pass
            
        # Not found or error
        result = PyPiPackageInfo(name=package_name, exists=False)
        _PYPI_CACHE[package_name] = result
        return result

    def _guess_apt_package_name(self, import_name: str) -> Optional[str]:
        """
        Heuristically guess APT package name (commonly python3-<name>).
        NOTE: This does not verify existence against a remote repo, 
        but assumes standard naming conventions for Debian/Ubuntu.
        """
        # Common pattern: import foo -> python3-foo
        # We can add a list of known valid apt packages if we want to be stricter,
        # or just return the guess.
        
        # Simple heuristic:
        # Convert underscores to hyphens
        normalized = import_name.replace('_', '-').lower()
        return f"python3-{normalized}"

    def resolve_packages(self, imports: List[str]) -> Dict:
        """
        Resolve import names to Pip and Apt packages.
        Strategy: APT FIRST.
        
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
            
            # 1. Check Library.json (Explicit Mappings)
            if imp in self.mappings:
                mapping = self.mappings[imp]
                
                # Check if APT is defined and preferred
                # If "apt" is present and not empty, we use it.
                # If "pip" is also present, we might technically need both?
                # Usually library.json defines dependencies.
                
                # Apt packages
                apt_pkgs = mapping.get("apt", [])
                if isinstance(apt_pkgs, str): apt_pkgs = [apt_pkgs]
                elif apt_pkgs is None: apt_pkgs = []
                
                # Pip packages
                pip_pkgs = mapping.get("pip", [])
                if isinstance(pip_pkgs, str): pip_pkgs = [pip_pkgs]
                elif pip_pkgs is None: pip_pkgs = []

                if apt_pkgs:
                    for pkg in apt_pkgs:
                        resolved["apt"].add(pkg)
                        resolved["reasons"][pkg] = f"Mapped from import '{imp}' (APT priority)"
                
                # Apt-First Strategy:
                # If we have a 'python3-*' package in apt list, it's likely a system generic replacement.
                # In that case, we SKIP the pip package to avoid conflict/redundancy.
                # If apt list only has libraries (e.g. libgl...), we still need the pip package.
                has_python_apt = any(p.startswith('python3-') or p.startswith('python-') for p in apt_pkgs)
                
                if pip_pkgs and not has_python_apt:
                    for pkg in pip_pkgs:
                        resolved["pip"].add(pkg)
                        resolved["reasons"][pkg] = f"Mapped from import '{imp}'"
                        
            else:
                # 2. Unknown Import - Try APT Heuristic FIRST
                # This corresponds to "Search for python3-<name>"
                # Since we can't search online easily, we use the heuristic guess.
                
                # User Requirement: "Search for python3-<name>... if not found... use pip"
                # To purely simulate "Search", we'd need a list.
                # Without a list, we might assume it exists if it's a "common" library?
                # Or we can just default to the heuristic and let the user correct it if apt fails?
                # "Apt-First" implies we should TRY apt.
                
                # Let's try to map it to python3-<name>
                apt_candidate = self._guess_apt_package_name(imp)
                
                # We can't verify 'apt_candidate' existence easily on Windows host.
                # However, for the sake of "Apt-First", we can tentatively add it to 'apt' 
                # OR we could rely on PyPI check first, then map to apt?
                
                # compromise: We will use PyPI to confirm it's a real package names.
                # If it is real, we map it to python3-<name> and put it in APT list
                # (Assuming 'python3-<pypi_name>' is the standard).
                
                pypi_candidate, confirmed, suggestion = self.guess_package_name(imp)
                
                if confirmed:
                    # It's a valid package. Prefer APT version.
                    # e.g. 'requests' -> 'python3-requests'
                    normalized_name = pypi_candidate if pypi_candidate else imp
                    apt_guess = f"python3-{normalized_name.replace('_', '-').lower()}"
                    
                    resolved["apt"].add(apt_guess)
                    resolved["reasons"][apt_guess] = f"Inferred Apt package for '{imp}' (Apt-First Strategy)"
                    print(f"[CodeAnalyzer] Apt-First: '{imp}' -> '{apt_guess}'")
                    
                    # Do NOT add to pip list (User requirement: "put in apt list... not pip list")
                else:
                     # Not found on PyPI either.
                     # Fallback to original behavior: add to unresolved
                    resolved["unresolved"].add(imp) # Use original import name as candidate
                    resolved["reasons"][imp] = f"Unconfirmed import '{imp}' (not in library.json, not found on PyPI)"
                    print(f"[CodeAnalyzer] Unresolved: '{imp}'")

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
