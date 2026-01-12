import json
import os
from typing import Dict, Union, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from lcr.utils.path_helper import get_resource_path

TEMPLATE_DIR = get_resource_path("templates")
IMAGE_DIR = Path(__file__).parent / "images"  # Images are generated artifacts, keep local

def render_dockerfile(config: Dict) -> str:
    """Render Dockerfile content from configuration dictionary."""
    context = {
        "base_image": config.get("base_image", "python:3.10-slim"),
        "use_archive_repo": config.get("use_archive_repo", False),
        "debian_release": config.get("debian_release", "stretch"),
        "system_packages": config.get("system_packages", []) or config.get("apt_packages", []),
        "trusted_hosts": config.get("trusted_hosts", ["pypi.python.org", "pypi.org", "files.pythonhosted.org"]),
        "pip_packages": config.get("pip_packages", []),
        "pip_config": config.get("pip_config", {}),
        "env_vars": config.get("env_vars", {}),
        "run_commands": config.get("run_commands", [])
    }
    
    # Load Template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("base.Dockerfile.j2")
    
    return template.render(context)

def save_definition(config: Dict, name: str) -> Path:
    """
    Save configuration dictionary to definitions directory as JSON.
    
    Args:
        config: Configuration dictionary
        name: Environment name (used for filename)
        
    Returns:
        Path to saved JSON file
    """
    definitions_dir = get_resource_path("definitions")
    
    # Ensure tag matches name if not set
    if "tag" not in config:
        config["tag"] = name
        
    safe_name = name.replace(" ", "_").lower()
    if not safe_name.endswith(".json"):
        safe_name += ".json"
        
    save_path = definitions_dir / safe_name
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
        
    return save_path

def generate_dockerfile(config_source: Union[str, Dict], output_dir: str = str(IMAGE_DIR)) -> tuple[str, str]:
    """
    Generate a Dockerfile from a JSON definition or config dict.
    Returns (tag, dockerfile_path).
    """
    if isinstance(config_source, str) or isinstance(config_source, Path):
        # Load from file
        config_path_obj = Path(config_source)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Config file not found: {config_source}")
            
        with open(config_source, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # Use provided dict
        config = config_source
    
    rendered = render_dockerfile(config)
    
    # Determine Output Filename
    tag = config.get("tag", "custom-image")
    safe_tag = tag.replace("-", "_").replace(":", "_")
    filename = f"Dockerfile.{safe_tag}"
    
    # Create output directory if needed
    out_path_obj = Path(output_dir)
    out_path_obj.mkdir(parents=True, exist_ok=True)
    
    output_path = out_path_obj / filename
    
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

