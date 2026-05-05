import hashlib
import json
import subprocess
from pathlib import PurePath
from typing import Dict, List, Optional, Any


class AuditMetadataService:
    """Collect audit metadata required by project standards."""

    def collect(
        self,
        image_name: str,
        script_path: str,
        script_path_rel: str,
        operation_type: str = "run",
        timestamp: str = "",
        targets: Optional[List[str]] = None,
        result: str = "unknown",
        released_size: int = 0,
        reason: str = "",
        param_payload: Optional[Dict] = None,
        input_files: Optional[List[str]] = None,
        input_files_rel: Optional[List[str]] = None,
        output_files: Optional[List[str]] = None,
        output_files_rel: Optional[List[str]] = None,
        log_path: Optional[str] = None,
        log_path_rel: Optional[str] = None,
        required_imports: Optional[List[str]] = None,
        environment_capability: Optional[Dict[str, Any]] = None,
        mismatch_result: Optional[Dict[str, Any]] = None,
        guard_state: str = "unknown",
    ) -> Dict:
        relative_script_path = self._normalize_relative_path(script_path_rel)
        input_hashes = self._hash_path_pairs(input_files or [], input_files_rel or [])
        output_hashes = self._hash_path_pairs(output_files or [], output_files_rel or [])
        param_sha256 = self._sha256_json(param_payload or {})
        image_digest = self._resolve_image_digest(image_name)
        git_commit_hash = self._resolve_git_commit_hash()
        metadata: Dict = {
            "operation_type": operation_type,
            "timestamp": timestamp,
            "targets": sorted(set(targets or [])),
            "result": result,
            "released_size": released_size,
            "reason": reason,
            # Required provenance
            "image_digest": image_digest,
            "container_image_digest": image_digest,
            "git_commit": git_commit_hash,
            "git_commit_hash": git_commit_hash,
            "script_path_rel": relative_script_path,
            "script_sha256": self._sha256_file(script_path),
            "param_hash": param_sha256,
            "input_hashes": input_hashes,
            "output_hashes": output_hashes,
            "log_hash": "unavailable",
            "log_path_rel": "",
            # Extended audit schema (reference standards / roadmap)
            "required_imports": sorted(set(required_imports or [])),
            "environment_capability": environment_capability or {},
            "mismatch_result": mismatch_result or {},
            "guard_state": guard_state,
            "guard_triggered": guard_state == "blocked",
            "parameter_sha256": param_sha256,
            "input_sha256": input_hashes,
            "output_sha256": output_hashes,
            "log_sha256": "unavailable",
            "execution_log_sha256": "unavailable",
            "path_mode": "relative_only",
            "hashes": {
                "all_input_files": input_hashes,
                "all_output_files": output_hashes,
                "all_parameter_files": {"parameters.json": param_sha256},
                "audit_log_record": "unavailable",
            },
            "relative_paths": {
                "script": relative_script_path,
                "inputs": sorted(input_hashes.keys()),
                "outputs": sorted(output_hashes.keys()),
                "log": "",
            },
        }
        if log_path and log_path_rel:
            normalized_log_path = self._normalize_relative_path(log_path_rel)
            metadata["log_path_rel"] = normalized_log_path
            log_sha = self._sha256_file(log_path)
            metadata["log_hash"] = log_sha
            metadata["log_sha256"] = log_sha
            metadata["execution_log_sha256"] = log_sha
            metadata["hashes"]["audit_log_record"] = log_sha
            metadata["relative_paths"]["log"] = normalized_log_path
        return metadata

    def _normalize_relative_path(self, path_str: str) -> str:
        if not path_str or not str(path_str).strip():
            raise ValueError("relative path must not be empty")
        path = PurePath(path_str)
        if path.is_absolute():
            raise ValueError(f"script_path_rel must be relative: {path_str}")
        if any(part == ".." for part in path.parts):
            raise ValueError(f"relative path must stay within project root: {path_str}")
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
