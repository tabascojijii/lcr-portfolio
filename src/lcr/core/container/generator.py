import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from lcr.utils.path_helper import get_resource_path

TEMPLATE_DIR = get_resource_path("templates")
IMAGE_DIR = Path(__file__).parent / "images"  # Images are generated artifacts, keep local

def generate_dockerfile(config_path: str, output_dir: str = str(IMAGE_DIR)):
    """
    Generate a Dockerfile from a JSON definition using the base template.
    """
    config_path_obj = Path(config_path)
    if not config_path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Defaults and Pre-processing
    context = {
        "base_image": config.get("base_image", "python:3.10-slim"),
        "use_archive_repo": config.get("use_archive_repo", False),
        "debian_release": config.get("debian_release", "stretch"),
        "system_packages": config.get("system_packages", []) or config.get("apt_packages", []),
        "trusted_hosts": config.get("trusted_hosts", ["pypi.python.org", "pypi.org", "files.pythonhosted.org"]),
        "pip_packages": config.get("pip_packages", []),
        "env_vars": config.get("env_vars", {}),
        "run_commands": config.get("run_commands", [])
    }
    
    # Load Template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("base.Dockerfile.j2")
    
    rendered = template.render(context)
    
    # Determine Output Filename
    # Tag format: lcr-py36-ml-classic -> Dockerfile.py36_ml_classic (approx mapping)
    # The build script expects specific mapping, but usually we define tag -> file in build script.
    # Here let's save as 'Dockerfile.<tag_safe>'
    
    tag = config.get("tag", "custom-image")
    # Clean tag for filename (e.g., lcr-py36-ml-classic -> lcr_py36_ml_classic)
    # But usually build_images.py maps tags manually. 
    # We will output the file and return the filename + tag so the caller can update build mappings.
    
    safe_tag = tag.replace("-", "_").replace(":", "_")
    filename = f"Dockerfile.{safe_tag}"
    output_path = Path(output_dir) / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered)
        
    print(f"[Generator] Generated {output_path} for tag '{tag}'")
    return tag, str(output_path)

def generate_all(definitions_dir: str):
    """Generate Dockerfiles for all json files in directory."""
    def_dir = Path(definitions_dir)
    if not def_dir.exists():
        print(f"Definitions directory {def_dir} does not exist.")
        return

    for json_file in def_dir.glob("*.json"):
        generate_dockerfile(str(json_file))

if __name__ == "__main__":
    # Example usage
    defs_dir = get_resource_path("definitions")
    generate_all(str(defs_dir))

