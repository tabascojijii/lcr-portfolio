import hashlib
from pathlib import Path

import pytest

from lcr.core.audit import AuditHashEvidenceUseCase


def test_generate_writes_hash_evidence_files(tmp_path: Path):
    (tmp_path / "artifacts").mkdir()
    target = tmp_path / "artifacts" / "traceability_matrix.md"
    target.write_text("traceability", encoding="utf-8")
    expected = hashlib.sha256(target.read_bytes()).hexdigest()

    use_case = AuditHashEvidenceUseCase(tmp_path)
    results = use_case.generate(
        run_id="run001",
        target_kind="artifact",
        relative_paths=["artifacts/traceability_matrix.md"],
    )

    output_rel = results["artifacts/traceability_matrix.md"]
    output_path = tmp_path / output_rel
    assert output_path.exists()
    assert output_path.name == "run001_artifact_artifacts__traceability_matrix.md.sha256"
    assert output_path.read_text(encoding="utf-8") == f"{expected}  artifacts/traceability_matrix.md\n"


def test_generate_rejects_non_relative_path(tmp_path: Path):
    use_case = AuditHashEvidenceUseCase(tmp_path)

    with pytest.raises(ValueError):
        use_case.generate("run001", "artifact", ["/absolute/path.txt"])
