import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from lcr.core.audit import AuditMetadataService


def test_collect_returns_expected_metadata(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    log_file = tmp_path / "run.log"
    script.write_text("print('ok')\n", encoding="utf-8")
    input_file.write_text("a,b\n1,2\n", encoding="utf-8")
    output_file.write_text("x,y\n3,4\n", encoding="utf-8")
    log_file.write_text("execution log\n", encoding="utf-8")
    expected_sha = hashlib.sha256(script.read_bytes()).hexdigest()
    expected_param_hash = hashlib.sha256(b'{"mode":"auto","retries":1}').hexdigest()
    expected_input_hash = hashlib.sha256(input_file.read_bytes()).hexdigest()
    expected_output_hash = hashlib.sha256(output_file.read_bytes()).hexdigest()
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
        param_payload={"mode": "auto", "retries": 1},
        input_files=[str(input_file)],
        input_files_rel=["data/input.csv"],
        output_files=[str(output_file)],
        output_files_rel=["results/output.csv"],
        log_path=str(log_file),
        log_path_rel="logs/run.log",
    )

    assert metadata["image_digest"] == "repo/image@sha256:abc"
    assert metadata["git_commit_hash"] == "deadbeef"
    assert metadata["script_path_rel"] == "rel/script.py"
    assert metadata["script_sha256"] == expected_sha
    assert metadata["param_hash"] == expected_param_hash
    assert metadata["input_hashes"] == {"data/input.csv": expected_input_hash}
    assert metadata["output_hashes"] == {"results/output.csv": expected_output_hash}
    assert metadata["log_path_rel"] == "logs/run.log"
    assert metadata["log_hash"] == expected_log_hash
    assert metadata["relative_paths"] == {
        "script": "rel/script.py",
        "inputs": ["data/input.csv"],
        "outputs": ["results/output.csv"],
        "log": "logs/run.log",
    }


def test_collect_falls_back_when_image_or_git_unavailable(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("x=1\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    service = AuditMetadataService()
    metadata = service.collect("missing-image", str(script), str(Path("script.py")))

    assert metadata["image_digest"] == "unavailable:missing-image"
    assert metadata["git_commit_hash"] == "unavailable"
    assert metadata["input_hashes"] == {}
    assert metadata["output_hashes"] == {}
    assert metadata["log_hash"] == "unavailable"
    assert metadata["relative_paths"] == {
        "script": "script.py",
        "inputs": [],
        "outputs": [],
        "log": "",
    }


def test_collect_normalizes_relative_script_path(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    service = AuditMetadataService()
    metadata = service.collect("img", str(script), r"nested\script.py")

    assert metadata["script_path_rel"] == "nested/script.py"


def test_collect_rejects_absolute_script_rel_path(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    service = AuditMetadataService()

    with pytest.raises(ValueError):
        service.collect("img", str(script), str(script.resolve()))


def test_collect_rejects_parent_traversal_in_relative_paths(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    service = AuditMetadataService()

    with pytest.raises(ValueError):
        service.collect("img", str(script), "../script.py")


def test_collect_rejects_empty_relative_script_path(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=""),
    )
    service = AuditMetadataService()

    with pytest.raises(ValueError):
        service.collect("img", str(script), "")
