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
        pass
    
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

    def resolve_runtime(self, search_terms: List[str], version_hint: str = "unknown") -> ImageRule:
        """
        Resolve best runtime based on search terms (keywords/libs) and version.
        Replaces 'select_image' with more robust matching.
        """
        best_rule = self.IMAGE_RULES[-1] # Default to latest 3.x
        best_score = -999
        
        # Search Terms Set
        terms_set = set(search_terms)

        for rule in self.IMAGE_RULES:
            # 1. Version Compatibility
            if not self._check_version_compat(version_hint, rule['version']):
                continue
                
            # 2. Score Calculation
            score = 0
            if rule['version'] == version_hint:
                score += 50
            
            # Library/Keyword Matching
            rule_libs = set(rule.get('libs', []))
            rule_triggers = set(rule.get('triggers', []))
            all_criteria = rule_libs.union(rule_triggers)
            
            if all_criteria:
                matched = all_criteria.intersection(terms_set)
                missing = rule_libs - terms_set # Only penalize missing 'required' libs
                
                score += len(matched) * 20
                score -= len(missing) * 10
                
                # Bonus for trigger match
                if rule_triggers.intersection(terms_set):
                    score += 30
            
            if score > best_score:
                best_score = score
                best_rule = rule
                
        return best_rule
        
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
        output_dir: Optional[str] = None
    ) -> RunConfig:
        """
        Prepare Docker run configuration with separate input/output mounts.
        """
        import datetime
        
        # Select image rule
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
