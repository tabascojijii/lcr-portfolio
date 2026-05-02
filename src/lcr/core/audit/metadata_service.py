import hashlib
import subprocess
from typing import Dict


class AuditMetadataService:
    """Collect audit metadata required by project standards."""

    def collect(self, image_name: str, script_path: str, script_path_rel: str) -> Dict[str, str]:
        return {
            "image_digest": self._resolve_image_digest(image_name),
            "git_commit_hash": self._resolve_git_commit_hash(),
            "script_path_rel": script_path_rel,
            "script_sha256": self._sha256_file(script_path),
        }

    def _resolve_image_digest(self, image_name: str) -> str:
        inspect = subprocess.run(
            ["docker", "image", "inspect", image_name, "--format", "{{index .RepoDigests 0}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if inspect.returncode != 0:
            return f"unavailable:{image_name}"
        value = inspect.stdout.strip()
        return value or f"unavailable:{image_name}"

    def _resolve_git_commit_hash(self) -> str:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode != 0:
            return "unavailable"
        return out.stdout.strip()

    def _sha256_file(self, path_str: str) -> str:
        h = hashlib.sha256()
        with open(path_str, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
