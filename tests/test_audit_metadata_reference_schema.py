import hashlib
from types import SimpleNamespace

from lcr.core.audit import AuditMetadataService


def test_collect_includes_reference_schema_fields(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    log_file = tmp_path / "run.log"
    script.write_text("print('ok')\n", encoding="utf-8")
    log_file.write_text("execution log\n", encoding="utf-8")
    expected_log_hash = hashlib.sha256(log_file.read_bytes()).hexdigest()

    def fake_run(args, capture_output, text, check):
        if args[:3] == ["docker", "image", "inspect"]:
            return SimpleNamespace(returncode=0, stdout="repo/image@sha256:abc\n")
        if args[:3] == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="deadbeef\n")
        return SimpleNamespace(returncode=1, stdout="")

    monkeypatch.setattr("subprocess.run", fake_run)
    service = AuditMetadataService()
    metadata = service.collect(
        "some-image",
        str(script),
        "rel/script.py",
        param_payload={"mode": "auto"},
        required_imports=["numpy", "cv2", "numpy"],
        environment_capability={"python": "3.10", "imports": ["numpy"]},
        mismatch_result={"missing": ["cv2"]},
        guard_state="blocked",
        log_path=str(log_file),
        log_path_rel="logs/run.log",
    )

    assert metadata["required_imports"] == ["cv2", "numpy"]
    assert metadata["environment_capability"] == {"python": "3.10", "imports": ["numpy"]}
    assert metadata["mismatch_result"] == {"missing": ["cv2"]}
    assert metadata["guard_state"] == "blocked"
    assert metadata["parameter_sha256"] == metadata["param_hash"]
    assert metadata["log_sha256"] == expected_log_hash
    assert metadata["log_hash"] == expected_log_hash
