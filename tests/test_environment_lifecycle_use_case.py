from datetime import datetime, timezone

import pytest

from lcr.core.container.lifecycle_use_cases import (
    DeleteExecutionPolicy,
    EnvironmentLifecycleUseCase,
    EnvironmentRecord,
)


def _record(env_id, protected=False, last_used_at=None, usage_count=0, category="legacy"):
    return EnvironmentRecord(
        env_id=env_id,
        display_name=env_id,
        description="desc",
        tags=["a"],
        category=category,
        protected=protected,
        last_used_at=last_used_at,
        usage_count=usage_count,
    )


def test_extract_unused_respects_protection_usage_and_age():
    use_case = EnvironmentLifecycleUseCase()
    now = datetime(2026, 5, 4, tzinfo=timezone.utc)
    records = [
        _record("old", usage_count=3, last_used_at="2026-01-01T00:00:00Z"),
        _record("fresh", usage_count=4, last_used_at="2026-05-01T00:00:00Z"),
        _record("never-used", usage_count=0, last_used_at=None),
        _record("protected-old", protected=True, usage_count=9, last_used_at="2025-01-01T00:00:00Z"),
    ]
    result = use_case.extract_unused(records, stale_days=30, now_utc=now)
    assert [r.env_id for r in result] == ["old", "never-used"]


def test_bulk_delete_uses_two_step_token_and_continues_on_failure():
    use_case = EnvironmentLifecycleUseCase()
    records = [_record("ok-1"), _record("ng"), _record("ok-2"), _record("keep", protected=True)]
    preview = use_case.build_delete_preview(records, ["ok-1", "ng", "ok-2", "keep"])
    assert preview.protected_ids == ["keep"]

    deleted = []

    def _delete_fn(env_id):
        if env_id == "ng":
            raise RuntimeError("boom")
        deleted.append(env_id)

    with pytest.raises(ValueError):
        use_case.execute_bulk_delete(preview, "bad-token", _delete_fn)

    result = use_case.execute_bulk_delete(preview, preview.confirmation_token, _delete_fn)
    assert result["deleted"] == ["ok-1", "ok-2"]
    assert result["failed"] == ["ng"]
    assert result["skipped_protected"] == ["keep"]
    assert result["rolled_back"] == []
    assert result["rollback_failed"] == []


def test_bulk_delete_rolls_back_when_policy_requires_it():
    use_case = EnvironmentLifecycleUseCase()
    records = [_record("ok-1"), _record("ng"), _record("ok-2")]
    preview = use_case.build_delete_preview(records, ["ok-1", "ng", "ok-2"])
    deleted = []
    rolled_back = []

    def _delete_fn(env_id):
        if env_id == "ng":
            raise RuntimeError("boom")
        deleted.append(env_id)

    def _rollback_fn(env_id):
        rolled_back.append(env_id)

    result = use_case.execute_bulk_delete(
        preview,
        preview.confirmation_token,
        _delete_fn,
        rollback_fn=_rollback_fn,
        policy=DeleteExecutionPolicy(rollback_on_any_failure=True),
    )
    assert result["failed"] == ["ng"]
    assert result["rolled_back"] == ["ok-2", "ok-1"]
    assert rolled_back == ["ok-2", "ok-1"]


def test_bulk_delete_stops_on_failure_threshold():
    use_case = EnvironmentLifecycleUseCase()
    records = [_record("ng-1"), _record("ng-2"), _record("ok")]
    preview = use_case.build_delete_preview(records, ["ng-1", "ng-2", "ok"])
    called = []

    def _delete_fn(env_id):
        called.append(env_id)
        if env_id.startswith("ng"):
            raise RuntimeError("boom")

    result = use_case.execute_bulk_delete(
        preview,
        preview.confirmation_token,
        _delete_fn,
        policy=DeleteExecutionPolicy(stop_on_failure_count=1),
    )
    assert result["failed"] == ["ng-1"]
    assert called == ["ng-1"]


def test_cleanup_targets_are_restricted_to_dangling_or_unused_image():
    use_case = EnvironmentLifecycleUseCase()
    selected = use_case.select_cleanup_targets(
        [
            {"kind": "dangling_image", "id": "d1"},
            {"kind": "unused_image", "id": "u1"},
            {"kind": "build_cache", "id": "b1"},
            {"kind": "volume", "id": "v1"},
        ]
    )
    assert selected == [{"kind": "dangling_image", "id": "d1"}, {"kind": "unused_image", "id": "u1"}]


def test_update_metadata_keeps_internal_id_immutable_and_validates_fields():
    use_case = EnvironmentLifecycleUseCase()
    record = _record("fixed-id", category="base")

    updated = use_case.update_metadata(
        record,
        {"display_name": "  New Name  ", "description": "  new desc ", "tags": ["z", "z", "x"], "category": "custom"},
    )
    assert updated.env_id == "fixed-id"
    assert updated.display_name == "New Name"
    assert updated.description == "new desc"
    assert updated.tags == ["x", "z"]
    assert updated.category == "custom"

    with pytest.raises(ValueError):
        use_case.update_metadata(record, {"env_id": "changed"})
