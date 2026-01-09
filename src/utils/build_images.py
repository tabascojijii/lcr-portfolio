import subprocess
import sys
import json
from pathlib import Path

# Add src to path to import generator
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root / "src"))

from lcr.core.container import generator

# 1. Base/Legacy Images
# Manual mapping for files that don't come from the generator
LEGACY_IMAGES = {
    "lcr-py27-cv2": "src/lcr/core/container/images/Dockerfile.py27_cv",
}

def build_images():
    print(f"--- LCR Image Builder ---")
    print(f"Project Root: {project_root}")
    
    # 1. Run Generator to ensure Dockerfiles are up to date
    definitions_dir = project_root / "src/lcr/core/container/definitions"
    print(f"\n[Generation] Running generator on {definitions_dir.name}...")
    generator.generate_all(str(definitions_dir))

    # 2. Collect All Targets
    # Start with legacy
    targets = LEGACY_IMAGES.copy()
    
    # Add generated targets from definitions
    if definitions_dir.exists():
        for def_file in definitions_dir.glob("*.json"):
            try:
                with open(def_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tag = data.get('tag')
                    # Match generator's filename logic
                    safe_tag = tag.replace("-", "_").replace(":", "_")
                    
                    # Assume generator output path relative to project root
                    rel_path = f"src/lcr/core/container/images/Dockerfile.{safe_tag}"
                    targets[tag] = rel_path
            except Exception as e:
                print(f"[WARN] Failed to read definition {def_file}: {e}")

    success_count = 0
    
    print(f"\n[Build] Found {len(targets)} images to build.")
    
    for tag_name, rel_path in targets.items():
        dockerfile_path = project_root / rel_path
        
        if not dockerfile_path.exists():
            print(f"\n[SKIP] Dockerfile not found: {dockerfile_path}")
            continue
            
        print(f"\n[{tag_name}] Building from {rel_path}...")
        
        cmd = [
            "docker", "build",
            "-t", tag_name,
            "-f", str(dockerfile_path),
            "--platform", "linux/amd64", 
            "."
        ]
        
        try:
            subprocess.run(cmd, cwd=project_root, check=True)
            print(f"[OK] SUCCESS: {tag_name}")
            success_count += 1
        except subprocess.CalledProcessError:
            print(f"[FAIL] Failed to build {tag_name}")
            # Do not sys.exit(1) here, continue to next
        except FileNotFoundError:
            print("[ERROR] 'docker' command not found. Is Docker Desktop running?")
            sys.exit(1)
            
    print("\n" + "="*30)
    if success_count == len(targets):
        print(f"COMPLETE: All {success_count} images are ready.")
    else:
        print(f"PARTIAL: {success_count}/{len(targets)} images built.")
        # Only exit 1 if we wanted strict success, but for now allow partial
        sys.exit(1 if success_count == 0 else 0)

if __name__ == "__main__":
    build_images()