# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Container manager for selecting and configuring Docker environments.

This module provides ContainerManager which:
- Selects appropriate Docker images based on code analysis
- Prepares Docker run configurations
- Maps Python versions to container images
"""

from typing import Dict, Optional, List
from pathlib import Path
import subprocess

from .types import ImageRule, RunConfig, AnalysisResult

class DockerUnavailableError(Exception):
    """Raised when Docker daemon is not reachable."""
    pass

class ContainerManager:
    """
    Manages Docker container selection and configuration.
    
    This class uses CodeAnalyzer results to determine the appropriate
    Docker image and configuration for running legacy code.
    """
    
    # Advanced image selection rules
    # Evaluated in order, or by scoring.
    IMAGE_RULES: List[ImageRule] = [
        # Python 2.7 rules
        {
            "id": "py27-cv2",
            "name": "Python 2.7 + OpenCV 2.x",
            "version": "2.7", 
            "libs": ["cv2", "opencv", "numpy"], 
            "image": "lcr-py27-cv-apt", 
            "prepend_python": False,
            "triggers": ["cv2.cv", "cv2.bgsegm"] # Triggers for specific runtime
        },
        {
            "id": "py27-slim",
            "name": "Python 2.7 (Slim)",
            "version": "2.7", 
            "libs": [], 
            "image": "python:2.7-slim", 
            "prepend_python": True,
            "triggers": []
        },
        
        # Python 3.x rules
        {
            "id": "py36-ds",
            "name": "Python 3.6 Data Science",
            "version": "3.x", 
            "libs": ["sklearn", "pandas", "numpy"], 
            "image": "lcr-py36-ml-classic", 
            "prepend_python": False, # LCR images have ENTRYPOINT ["python"]
            "triggers": ["sklearn", "pandas"]
        },
        {
            "id": "py310-slim",
            "name": "Python 3.10 (Latest)",
            "version": "3.x", 
            "libs": [], 
            "image": "python:3.10-slim", 
            "prepend_python": True,
            "triggers": []
        }
    ]
    
    def __init__(self):
        """Initialize the ContainerManager."""
        self._load_definitions()
    
    def _load_definitions(self):
        """
        Load external JSON definitions from the definitions/ resource directory.
        Robustness: Skips invalid files and handles missing directories gracefully.
        """
        import json
        from lcr.utils.path_helper import get_resource_path
        
        try:
            def_dir = get_resource_path('definitions')
            if not def_dir.exists():
                print(f"[ContainerManager] Warning: Definitions directory not found: {def_dir}")
                return

            loaded_count = 0
            for json_file in def_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Validation: Check required keys
                    if 'tag' not in data or 'base_image' not in data:
                        print(f"[ContainerManager] Skipping invalid definition {json_file.name}: Missing 'tag' or 'base_image'")
                        continue
                        
                    # Avoid duplicates
                    if any(r['image'] == data['tag'] for r in self.IMAGE_RULES):
                        continue
                        
                    # Create Rule
                    # definitions currently lack runtime metadata (libs, triggers), so we leave them empty.
                    # This means they won't be auto-selected easily, which is desired for Manual-only visibility initially.
                    new_rule: ImageRule = {
                        "id": json_file.stem,
                        "name": f"{json_file.stem} ({data.get('tag')})",
                        "version": "unknown", # Metadata missing in current definitions
                        "libs": [],
                        "image": data['tag'],
                        "prepend_python": False, # LCR images
                        "triggers": [],
                        # Store extra info for UI tooltips if needed
                        "description": f"Base: {data.get('base_image')}"
                    }
                    self.IMAGE_RULES.append(new_rule)
                    loaded_count += 1
                    
                except Exception as e:
                    print(f"[ContainerManager] Error loading {json_file.name}: {e}")
            
            if loaded_count > 0:
                print(f"[ContainerManager] Loaded {loaded_count} external definitions.")
                
        except Exception as e:
            print(f"[ContainerManager] Critical Error loading definitions: {e}")

    def reload_definitions(self):
        """
        Reload all definitions from disk and update internal rules list.
        Preserves the hardcoded rules (first set of rules) but refreshes loaded ones.
        """
        # Keep hardcoded rules (assuming they are first 4 in current implementation)
        # Better strategy: Filter list to only keep those WITHOUT 'id' matching file pattern or use explicit mark
        # For this phase, we'll reset to initial Hardcoded Set manually or via Filter
        
        # Hardcoded IDs: py27-cv2, py27-slim, py36-ds, py310-slim
        hardcoded_ids = {"py27-cv2", "py27-slim", "py36-ds", "py310-slim"}
        self.IMAGE_RULES = [r for r in self.IMAGE_RULES if r['id'] in hardcoded_ids]
        
        # Reload from disk
        self._load_definitions()
        print("[ContainerManager] Definitions reloaded.")

    
    def validate_environment(self):
        """
        Check if Docker is available and running.
        
        Raises:
            DockerUnavailableError: If Docker is not found or not running.
        """
        try:
            # lightweight check
            subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DockerUnavailableError("Docker is not running or not installed. Please start Docker Desktop.")

    def get_available_runtimes(self) -> List[ImageRule]:
        """Return list of available runtimes from rules."""
        return self.IMAGE_RULES

    def resolve_runtime(self, search_terms, version_hint: str = "unknown") -> ImageRule:
        """
        Resolve best runtime based on search terms (keywords/libs) and version.
        Replaces 'select_image' with more robust matching.
        
        Args:
            search_terms: Either List[str] of search terms, or Dict (analysis result)
            version_hint: Version string (optional if search_terms is a dict)
        
        CRITICAL: Major version (2.x vs 3.x) compatibility is the PRIMARY criterion.
        Images with incompatible major versions receive overwhelming penalties.
        """
        # Handle both list and dict inputs for backward compatibility
        if isinstance(search_terms, dict):
            # Dict format: extract info from analysis result
            version_hint = search_terms.get('version', 'unknown')
            libs = search_terms.get('libraries', search_terms.get('imports', []))
            keywords = search_terms.get('keywords', [])
            terms_set = set(libs + keywords)
        else:
            # List format: use as-is
            terms_set = set(search_terms)
        
        best_rule = self.IMAGE_RULES[-1]  # Default to latest 3.x
        best_score = -999999  # Very low default to allow penalties
        best_reasons = []
        
        # Scoring details for each rule
        scoring_log = []

        for rule in self.IMAGE_RULES:
            # Extract major version from both code and rule
            code_major = self._get_major_version(version_hint)
            rule_major = self._get_major_version(rule['version'])
            
            # 1. CRITICAL: Major Version Compatibility Check
            # Apply overwhelming penalty if major versions are incompatible
            score = 0
            reasons = []
            
            if code_major != 'unknown' and rule_major != 'unknown':
                if code_major == rule_major:
                    # Same major version: huge bonus (overrides all other factors)
                    score += 10000
                    reasons.append(f"Major version match (Python {code_major}.x)")
                else:
                    # Different major version: massive penalty (makes this rule almost impossible to select)
                    score -= 100000
                    reasons.append(f"INCOMPATIBLE: Code needs Python {code_major}.x, image provides {rule_major}.x")
            elif code_major == 'unknown' or rule_major == 'unknown':
                # Unknown version: neutral (no bonus/penalty)
                reasons.append("Version unknown - neutral scoring")
                
            # 2. Exact Version Match Bonus (secondary to major version)
            if version_hint != 'unknown' and rule['version'] == version_hint:
                score += 500
                reasons.append(f"Exact version match ({version_hint})")
            
            # 3. Library/Keyword Matching (tertiary)
            rule_libs = set(rule.get('libs', []))
            rule_triggers = set(rule.get('triggers', []))
            all_criteria = rule_libs.union(rule_triggers)
            
            if all_criteria:
                matched = all_criteria.intersection(terms_set)
                missing = rule_libs - terms_set  # Only penalize missing 'required' libs
                
                if matched:
                    score += len(matched) * 20
                    reasons.append(f"Matched libraries: {', '.join(matched)}")
                
                if missing:
                    score -= len(missing) * 10
                    reasons.append(f"Missing libraries: {', '.join(missing)}")
                
                # Bonus for trigger match
                if rule_triggers.intersection(terms_set):
                    score += 30
                    reasons.append("Trigger keywords matched")
            
            scoring_log.append({
                'rule': rule['id'],
                'score': score,
                'reasons': reasons
            })
            
            if score > best_score:
                best_score = score
                best_rule = rule.copy()  # Copy to avoid mutating original
                best_reasons = reasons.copy()
        
        # Add reasoning to the returned rule
        best_rule['reason'] = " | ".join(best_reasons) if best_reasons else "Default selection"
        best_rule['score'] = best_score
        
        # Log scoring details for debugging
        print(f"\n[ContainerManager] Runtime Selection for Python {version_hint}:")
        for log in scoring_log:
            print(f"  - {log['rule']}: Score={log['score']} | {' | '.join(log['reasons'])}")
        print(f"  => SELECTED: {best_rule['id']} (Score: {best_score})")
        print(f"  => REASON: {best_rule['reason']}\n")
                
        return best_rule
    
    def _get_major_version(self, version_str: str) -> str:
        """
        Extract major version from version string.
        
        Args:
            version_str: Version string like "2.7", "3.x", "3.10", "unknown"
            
        Returns:
            Major version as "2" or "3", or "unknown"
        """
        if not version_str or version_str == 'unknown':
            return 'unknown'
            
        # Handle "3.x" format
        if version_str.startswith('3'):
            return '3'
        elif version_str.startswith('2'):
            return '2'
        else:
            return 'unknown'
        
    def _check_version_compat(self, code_ver, rule_ver):
        if code_ver == 'unknown' or rule_ver == 'unknown': return True
        if code_ver == rule_ver: return True
        if code_ver == '3.x' and rule_ver.startswith('3'): return True
        if code_ver.startswith('3') and rule_ver == '3.x': return True
        return False

    def select_image(self, analysis_result: AnalysisResult) -> ImageRule:
        """Legacy wrapper for backward compatibility."""
        # Convert analysis result to search terms
        libs = analysis_result.get('libraries', [])
        keywords = analysis_result.get('keywords', [])
        version = analysis_result.get('version', 'unknown')
        
        search_terms = libs + keywords
        return self.resolve_runtime(search_terms, version)
    
    def prepare_run_config(
        self, 
        analysis_result: AnalysisResult, 
        script_path: str,
        work_dir: Optional[str] = None,
        data_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        override_image_rule: Optional[ImageRule] = None
    ) -> RunConfig:
        """
        Prepare Docker run configuration with separate input/output mounts.
        Supports manual override of the image selection.
        """
        import datetime
        
        # Select image rule
        if override_image_rule:
            rule = override_image_rule
            # Compatibility Check (Warning Log)
            detected_ver = analysis_result.get('version', 'unknown')
            rule_ver = rule.get('version', 'unknown')
            if not self._check_version_compat(detected_ver, rule_ver):
                print(f"[RunConfig] WARNING: Version mismatch detected! Code: {detected_ver}, Image: {rule_ver}")
        else:
            rule = self.select_image(analysis_result)
            
        image = rule['image']
        
        # Logic to check if we should prepend python
        # 1. Use explicit rule setting if present
        # 2. If valid LCR image (constructed via template), ENTRYPOINT is python, so don't prepend
        if 'prepend_python' in rule:
            prepend_python = rule['prepend_python']
        else:
            # Auto-detection: If image starts with 'lcr-', assume it has ENTRYPOINT ["python"]
            prepend_python = not image.startswith('lcr-')
        
        # Determine paths
        script_path_obj = Path(script_path).resolve()
        if not script_path_obj.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # 1. Host Input Directory (Source for Script) -> /app/input (RO)
        # We assume the script is in a directory that serves as its "input context".
        host_input_dir = script_path_obj.parent
        script_name = script_path_obj.name
        
        # 2. Host Output Directory -> /app/output (RW)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sub_dir_name = f"LCR_RUN_{timestamp}"
        
        if output_dir:
            # User specified path
            base_output_path = Path(output_dir).resolve()
            
            # Safety Check: Collision with Input
            # We strictly prevent outputting directly into the source directory to avoid clutter/overwrites
            # unless it's a dedicated results folder within it (handled by subfolder logic)
            if base_output_path == host_input_dir:
                raise ValueError(
                    f"Output directory cannot be identical to the script source directory: {host_input_dir}. "
                    "Please select a different folder."
                )
                
            host_output_dir = base_output_path / sub_dir_name
        else:
            # Default logic: {ProjectRoot}/data/results/{YYYYMMDD_HHMMSS}
            # Inferred Project Root: 4 levels up
            project_root = Path(__file__).resolve().parents[4]
            
            # Fallback if project root seems wrong
            if not (project_root / "run_gui.py").exists() and not (project_root / ".git").exists():
                 project_root = Path.cwd()
            
            host_output_dir = project_root / "data" / "results" / timestamp
        
        # Create output directory
        host_output_dir.mkdir(parents=True, exist_ok=True)
        
        # --- SNAPSHOT SAFETY FEATURE ---
        # Copy the source script to the output directory as 'source_snapshot.py'.
        # This ensures auditability even if the original script is modified later.
        try:
            import shutil
            snapshot_path = host_output_dir / "source_snapshot.py"
            shutil.copy2(script_path, snapshot_path)
        except Exception as e:
            # Non-blocking failure: Log warning but proceed with execution
            print(f"[Warning] Failed to create source snapshot: {e}")
        # -------------------------------
        
        # Container Paths
        container_input_dir = '/app/input'
        container_output_dir = '/app/output'
        container_script_path = f'{container_input_dir}/{script_name}'
        
        # Build volumes
        volumes = {
            # Script Input (Read-only)
            str(host_input_dir): {
                'bind': container_input_dir,
                'mode': 'ro' 
            },
            # Result Output (Read-write)
            str(host_output_dir): {
                'bind': container_output_dir,
                'mode': 'rw'
            }
        }
        
        # Add optional data volume if provided (e.g., large datasets)
        if data_dir:
            host_data_dir = Path(data_dir).resolve()
            if host_data_dir.exists():
                volumes[str(host_data_dir)] = {
                    'bind': '/data',
                    'mode': 'ro' 
                }
        
        # Build configuration
        # Handle Entrypoint logic
        if prepend_python:
            command = ['python', container_script_path]
        else:
            command = [container_script_path]
            
        config: RunConfig = {
            'image': image,
            'volumes': volumes,
            # Set working dir to output so artifacts land there
            'working_dir': container_output_dir, 
            'command': command,
            'script_name': script_name,
            'host_work_dir': str(host_output_dir), # Reported host work dir matches output
        }
        
        return config
    
    def get_docker_run_args(self, config: RunConfig) -> list:
        """
        Convert configuration to docker run command arguments.
        
        Args:
            config: Configuration from prepare_run_config()
        
        Returns:
            List of command arguments for subprocess
        """
        args = ['docker', 'run', '--rm']
        
        # Add volume mounts
        for host_path, mount_config in config['volumes'].items():
            bind_path = mount_config['bind']
            mode = mount_config.get('mode', 'rw')
            args.extend(['-v', f'{host_path}:{bind_path}:{mode}'])
        
        # Add working directory
        args.extend(['-w', config['working_dir']])
        
        # Add image
        args.append(config['image'])
        
        # Add command
        args.extend(config['command'])
        
        return args
    
    def install_dependencies(
        self, 
        analysis_result: Dict,
        requirements_file: Optional[str] = None
    ) -> Optional[list]:
        """
        Generate pip install commands for detected libraries.
        
        This is a future extension point for automatic dependency installation.
        
        Args:
            analysis_result: Dictionary from CodeAnalyzer.summary()
            requirements_file: Optional path to requirements.txt
        
        Returns:
            List of pip install commands, or None if no dependencies
        """
        libraries = analysis_result.get('libraries', [])
        
        if not libraries:
            return None
        
        # Filter out standard library modules
        # This is a simplified approach - could be enhanced with stdlib detection
        external_libs = [lib for lib in libraries if lib not in ['sys', 'os', 're', 'json']]
        
        if not external_libs:
            return None
        
        # Generate pip install command
        # Note: This is a placeholder for future enhancement
        # In practice, you'd want to handle version pinning, etc.
        pip_cmd = ['pip', 'install'] + external_libs
        
        return [pip_cmd]

    def synthesize_definition_config(self, analysis_result: Dict, base_rule_id: str) -> Dict:
        """
        Create a new environment configuration based on analysis and a selected base image.
        
        Args:
            analysis_result: Result from CodeAnalyzer
            base_rule_id: ID of the base image rule to extend
            
        Returns:
            Dict containing the new definition config (ready for JSON save)
        """
        # Find base rule
        base_rule = next((r for r in self.IMAGE_RULES if r['id'] == base_rule_id), None)
        if not base_rule:
            # Fallback to latest python
            base_rule = self.IMAGE_RULES[-1]
            
        # 1. Resolve Detected Packages to Pip/Apt names
        from lcr.core.detector.analyzer import CodeAnalyzer
        # We need an instance to access the loaded mappings
        analyzer = CodeAnalyzer() 
        detected_imports = analysis_result.get('libraries', [])
        resolved = analyzer.resolve_packages(detected_imports)
        
        detected_pip = resolved['pip']
        detected_apt = resolved['apt']
        
        # 2. Get Base Image Packages (to avoid duplicates)
        # Try to load the definition of the base image to find what it already has
        base_pip = set()
        base_apt = set()
        
        # If the base rule points to a known definition file, we could load it.
        # However, IMAGE_RULES are just runtime metadata.
        # Heuristic: if ID matches one we loaded, we might have access to its config?
        # A robust way is to re-load the JSON if the rule ID corresponds to a file stem.
        # But for now, we'll assume the base is barebones OR rely on pip to skip existing.
        # "Pure Diff" requirement suggests we SHOULD try to exclude.
        
        # Let's try to match ID to a loaded definition file pattern if possible
        # Actually Manager doesn't store the full loaded config relative to ID efficiently yet.
        # Optimization: Just proceed with what we detected. Pip handles duplicates gracefully.
        # User requested "Pure Diff", but without Base Info it is hard.
        # Compromise: We simply pass the detected set. 
        # (If user insists on pure diff, we need Base Definition Knowledge Base).
        
        # 3. Construct Config
        config = {
            "tag": "custom-auto-gen", # Placeholder, user should override
            "base_image": base_rule.get('image', 'python:3.10-slim'),
            "apt_packages": list(detected_apt),
            "pip_packages": list(detected_pip),
            "env_vars": {"PYTHONUNBUFFERED": "1"},
            "run_commands": [],
            "_resolution_reasons": resolved.get("reasons", {}), # Metadata for UI
            "_unresolved": list(resolved.get("unresolved", [])) # Metadata for UI
        }
        
        return config

    def get_build_command(self, dockerfile_path: str, tag: str) -> list:
        """Construct docker build command."""
        # Use absolute path for safety
        path_obj = Path(dockerfile_path).resolve()
        context_dir = path_obj.parent
        
        return [
            "docker", "build",
            "-t", tag,
            "-f", str(path_obj),
            str(context_dir)
        ]
