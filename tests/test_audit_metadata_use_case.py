from pathlib import Path

import pytest

from lcr.core.audit.use_cases import CollectAuditMetadataUseCase


class _HistoryStub:
    def __init__(self, root: Path):
        self.root = root

    def to_relative_path(self, p: str) -> str:
        return Path(p).resolve().relative_to(self.root).as_posix()


class _AuditStub:
    def __init__(self):
        self.captured = None

    def collect(self, image_name, script_path, script_path_rel, **kwargs):
        self.captured = (image_name, script_path, script_path_rel, kwargs)
        return {"ok": True, "script_path_rel": script_path_rel, **kwargs}


def test_collect_audit_use_case_converts_paths_to_relative(tmp_path):
    script = tmp_path / "sample.py"
    input_file = tmp_path / "in.txt"
    output_file = tmp_path / "out.txt"
    log_file = tmp_path / "run.log"
    script.write_text("print(1)\n", encoding="utf-8")
    input_file.write_text("in\n", encoding="utf-8")
    output_file.write_text("out\n", encoding="utf-8")
    log_file.write_text("log\n", encoding="utf-8")

    history = _HistoryStub(tmp_path.resolve())
    audit = _AuditStub()
    use_case = CollectAuditMetadataUseCase(history, audit)
    res = use_case.execute(
        "img",
        str(script),
        param_payload={"k": "v"},
        input_files=[str(input_file)],
        output_files=[str(output_file)],
        log_path=str(log_file),
    )

    assert res["script_path_rel"] == "sample.py"
    assert res["input_files_rel"] == ["in.txt"]
    assert res["output_files_rel"] == ["out.txt"]
    assert res["log_path_rel"] == "run.log"


def test_collect_audit_use_case_fails_safe_on_incomplete_metadata(tmp_path):
    script = tmp_path / "sample.py"
    script.write_text("print(1)\n", encoding="utf-8")
    history = _HistoryStub(tmp_path.resolve())

    class _IncompleteAuditStub:
        def collect(self, *args, **kwargs):
            return {
                "image_digest": "unavailable:image",
                "git_commit_hash": "unavailable",
                "script_path_rel": "sample.py",
                "script_sha256": "x",
                "parameter_sha256": "x",
                "input_sha256": {},
                "output_sha256": {},
                "log_sha256": "unavailable",
            }

    use_case = CollectAuditMetadataUseCase(history, _IncompleteAuditStub())
    with pytest.raises(ValueError):
        use_case.execute("img", str(script), fail_on_incomplete_audit=True)
