import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from lcr.core.audit import AuditMetadataService


def test_collect_returns_expected_metadata(tmp_path, monkeypatch):
    script = tmp_path / "script.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    expected_sha = hashlib.sha256(script.read_bytes()).hexdigest()

    def fake_run(args, capture_output, text, check):
        if args[:3] == ["docker", "image", "inspect"]:
            return SimpleNamespace(returncode=0, stdout="repo/image@sha256:abc\n")
        if args[:3] == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="deadbeef\n")
        return SimpleNamespace(returncode=1, stdout="")

    monkeypatch.setattr("subprocess.run", fake_run)
    service = AuditMetadataService()
    metadata = service.collect("some-image", str(script), "rel/script.py")

    assert metadata["image_digest"] == "repo/image@sha256:abc"
    assert metadata["git_commit_hash"] == "deadbeef"
    assert metadata["script_path_rel"] == "rel/script.py"
    assert metadata["script_sha256"] == expected_sha


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
