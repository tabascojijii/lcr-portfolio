import hashlib
import json
import subprocess
from pathlib import PurePath
from typing import Dict, List, Optional


class AuditMetadataService:
    """Collect audit metadata required by project standards."""

    def collect(
        self,
        image_name: str,
        script_path: str,
        script_path_rel: str,
        param_payload: Optional[Dict] = None,
        input_files: Optional[List[str]] = None,
        input_files_rel: Optional[List[str]] = None,
        output_files: Optional[List[str]] = None,
        output_files_rel: Optional[List[str]] = None,
        log_path: Optional[str] = None,
        log_path_rel: Optional[str] = None,
    ) -> Dict:
        relative_script_path = self._normalize_relative_path(script_path_rel)
        metadata: Dict = {
            "image_digest": self._resolve_image_digest(image_name),
            "git_commit_hash": self._resolve_git_commit_hash(),
            "script_path_rel": relative_script_path,
            "script_sha256": self._sha256_file(script_path),
            "param_hash": self._sha256_json(param_payload or {}),
            "input_hashes": self._hash_path_pairs(input_files or [], input_files_rel or []),
            "output_hashes": self._hash_path_pairs(output_files or [], output_files_rel or []),
            "log_hash": "unavailable",
            "log_path_rel": "",
        }
        if log_path and log_path_rel:
            metadata["log_path_rel"] = self._normalize_relative_path(log_path_rel)
            metadata["log_hash"] = self._sha256_file(log_path)
        return metadata

    def _normalize_relative_path(self, path_str: str) -> str:
        path = PurePath(path_str)
        if path.is_absolute():
            raise ValueError(f"script_path_rel must be relative: {path_str}")
        return path.as_posix()

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

    def _sha256_json(self, payload: Dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _hash_path_pairs(self, abs_paths: List[str], rel_paths: List[str]) -> Dict[str, str]:
        if len(abs_paths) != len(rel_paths):
            raise ValueError("abs_paths and rel_paths must have the same length")
        result: Dict[str, str] = {}
        for abs_path, rel_path in zip(abs_paths, rel_paths):
            normalized = self._normalize_relative_path(rel_path)
            result[normalized] = self._sha256_file(abs_path)
        return result
