from pathlib import Path

import pytest

from lcr.core.audit.use_cases import CollectAuditMetadataUseCase


class _HistoryStub:
    def __init__(self, root: Path):
        self.root = root

    def to_relative_path(self, p: str) -> str:
        return Path(p).resolve().relative_to(self.root).as_posix()


class _CompleteAuditStub:
    def collect(self, *args, **kwargs):
        return {
            "operation_type": "run",
            "timestamp": "2026-05-05T00:00:00+09:00",
            "targets": ["t"],
            "result": "ok",
            "released_size": 0,
            "reason": "",
            "image_digest": "repo/image@sha256:" + "a" * 64,
            "container_image_digest": "repo/image@sha256:" + "a" * 64,
            "git_commit": "a" * 40,
            "git_commit_hash": "a" * 40,
            "script_path_rel": "sample.py",
            "script_sha256": "b" * 64,
            "required_imports": [],
            "environment_capability": {},
            "mismatch_result": {},
            "guard_triggered": False,
            "parameter_sha256": "c" * 64,
            "input_sha256": {"data/in.txt": "d" * 64},
            "output_sha256": {"data/out.txt": "e" * 64},
            "log_sha256": "f" * 64,
            "execution_log_sha256": "f" * 64,
            "path_mode": "relative_only",
            "hashes": {
                "all_input_files": {"data/in.txt": "d" * 64},
                "all_output_files": {"data/out.txt": "e" * 64},
                "all_parameter_files": {"parameters.json": "c" * 64},
                "audit_log_record": "f" * 64,
            },
        }


class _AbsolutePathModeStub(_CompleteAuditStub):
    def collect(self, *args, **kwargs):
        data = super().collect(*args, **kwargs)
        data["path_mode"] = "absolute"
        return data


class _BadHashStub(_CompleteAuditStub):
    def collect(self, *args, **kwargs):
        data = super().collect(*args, **kwargs)
        data["parameter_sha256"] = "not-a-sha"
        return data


class _BadCommitStub(_CompleteAuditStub):
    def collect(self, *args, **kwargs):
        data = super().collect(*args, **kwargs)
        data["git_commit_hash"] = "deadbeef"
        return data


def _build_use_case(tmp_path, audit_stub):
    script = tmp_path / "sample.py"
    script.write_text("print(1)\n", encoding="utf-8")
    history = _HistoryStub(tmp_path.resolve())
    return script, CollectAuditMetadataUseCase(history, audit_stub)


def test_data_integrity_required_fields_pass(tmp_path):
    script, use_case = _build_use_case(tmp_path, _CompleteAuditStub())

    metadata = use_case.execute("img", str(script), fail_on_incomplete_audit=True)

    assert metadata["path_mode"] == "relative_only"


def test_data_integrity_rejects_non_relative_path_mode(tmp_path):
    script, use_case = _build_use_case(tmp_path, _AbsolutePathModeStub())

    with pytest.raises(ValueError):
        use_case.execute("img", str(script), fail_on_incomplete_audit=True)


def test_data_integrity_rejects_invalid_sha256_format(tmp_path):
    script, use_case = _build_use_case(tmp_path, _BadHashStub())

    with pytest.raises(ValueError):
        use_case.execute("img", str(script), fail_on_incomplete_audit=True)


def test_data_integrity_rejects_non_40_hex_git_commit_hash(tmp_path):
    script, use_case = _build_use_case(tmp_path, _BadCommitStub())

    with pytest.raises(ValueError):
        use_case.execute("img", str(script), fail_on_incomplete_audit=True)
