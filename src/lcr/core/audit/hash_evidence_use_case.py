import hashlib
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable


class AuditHashEvidenceUseCase:
    """Generate per-artifact SHA-256 evidence files under artifacts/audit/hashes."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def generate(self, run_id: str, target_kind: str, relative_paths: Iterable[str]) -> Dict[str, str]:
        if not run_id.strip():
            raise ValueError("run_id must not be empty")
        if not target_kind.strip():
            raise ValueError("target_kind must not be empty")

        hashes_dir = self.project_root / "artifacts" / "audit" / "hashes"
        hashes_dir.mkdir(parents=True, exist_ok=True)

        results: Dict[str, str] = {}
        for rel_path in relative_paths:
            normalized = self._normalize_relative_path(rel_path)
            digest = self._sha256_file(self.project_root / normalized)
            normalized_token = normalized.as_posix().replace("/", "__")
            filename = f"{run_id}_{target_kind}_{normalized_token}.sha256"
            output_path = hashes_dir / filename
            output_path.write_text(f"{digest}  {normalized.as_posix()}\n", encoding="utf-8")
            results[normalized.as_posix()] = str(output_path.relative_to(self.project_root)).replace("\\", "/")
        return results

    def _normalize_relative_path(self, path_str: str) -> PurePosixPath:
        path = PurePosixPath(path_str)
        if path.is_absolute():
            raise ValueError(f"path must be relative: {path_str}")
        if any(part in ("", ".", "..") for part in path.parts):
            raise ValueError(f"path must stay within project root: {path_str}")
        return path

    @staticmethod
    def _sha256_file(path: Path) -> str:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
