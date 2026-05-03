from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


@dataclass(frozen=True)
class EnvironmentRecord:
    env_id: str
    display_name: str
    description: str
    tags: List[str]
    category: str
    protected: bool
    last_used_at: Optional[str]
    usage_count: int


@dataclass(frozen=True)
class DeletePreview:
    target_ids: List[str]
    protected_ids: List[str]
    deletable_ids: List[str]
    confirmation_token: str


@dataclass(frozen=True)
class DeleteExecutionPolicy:
    """Safety policy for staged deletion and rollback."""

    rollback_on_any_failure: bool = False
    stop_on_failure_count: Optional[int] = None


class EnvironmentLifecycleUseCase:
    """Application use case for environment lifecycle management."""

    def search(self, records: List[EnvironmentRecord], query: str = "", category: str = "") -> List[EnvironmentRecord]:
        q = query.strip().lower()
        cat = category.strip().lower()
        result: List[EnvironmentRecord] = []
        for record in records:
            if cat and record.category.lower() != cat:
                continue
            if q:
                text = " ".join([record.env_id, record.display_name, record.description, " ".join(record.tags)]).lower()
                if q not in text:
                    continue
            result.append(record)
        return result

    def extract_unused(
        self,
        records: List[EnvironmentRecord],
        stale_days: int,
        now_utc: Optional[datetime] = None,
    ) -> List[EnvironmentRecord]:
        now = now_utc or datetime.now(timezone.utc)
        result: List[EnvironmentRecord] = []
        for record in records:
            if record.protected:
                continue
            if record.usage_count > 0 and record.last_used_at:
                age_days = (now - _parse_iso_utc(record.last_used_at)).days
                if age_days >= stale_days:
                    result.append(record)
                continue
            if record.usage_count == 0:
                result.append(record)
        return result

    def build_delete_preview(self, records: List[EnvironmentRecord], target_ids: List[str]) -> DeletePreview:
        unique_targets = sorted(set(target_ids))
        by_id = {r.env_id: r for r in records}
        protected_ids = sorted([env_id for env_id in unique_targets if by_id.get(env_id) and by_id[env_id].protected])
        deletable_ids = sorted([env_id for env_id in unique_targets if by_id.get(env_id) and env_id not in protected_ids])
        return DeletePreview(
            target_ids=unique_targets,
            protected_ids=protected_ids,
            deletable_ids=deletable_ids,
            confirmation_token=_build_confirmation_token(deletable_ids),
        )

    def execute_bulk_delete(
        self,
        preview: DeletePreview,
        confirmation_token: str,
        delete_fn: Callable[[str], None],
        rollback_fn: Optional[Callable[[str], None]] = None,
        policy: Optional[DeleteExecutionPolicy] = None,
    ) -> Dict[str, List[str]]:
        if confirmation_token != preview.confirmation_token:
            raise ValueError("Second confirmation token mismatch.")
        active_policy = policy or DeleteExecutionPolicy()
        deleted: List[str] = []
        failed: List[str] = []
        rollback_failed: List[str] = []
        for env_id in preview.deletable_ids:
            try:
                delete_fn(env_id)
                deleted.append(env_id)
            except Exception:
                failed.append(env_id)
                if active_policy.stop_on_failure_count and len(failed) >= active_policy.stop_on_failure_count:
                    break
        rolled_back: List[str] = []
        if failed and active_policy.rollback_on_any_failure and rollback_fn:
            for env_id in reversed(deleted):
                try:
                    rollback_fn(env_id)
                    rolled_back.append(env_id)
                except Exception:
                    rollback_failed.append(env_id)
        return {
            "deleted": deleted,
            "failed": failed,
            "skipped_protected": list(preview.protected_ids),
            "rolled_back": rolled_back,
            "rollback_failed": rollback_failed,
        }

    def select_cleanup_targets(self, docker_candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Allow only dangling/unused image cleanup targets."""
        allowed_kinds = {"dangling_image", "unused_image"}
        return [item for item in docker_candidates if item.get("kind") in allowed_kinds]

    def update_metadata(self, record: EnvironmentRecord, patch: Dict[str, object]) -> EnvironmentRecord:
        if "env_id" in patch and patch["env_id"] != record.env_id:
            raise ValueError("Internal environment id is immutable.")
        display_name = str(patch.get("display_name", record.display_name)).strip()
        if not display_name:
            raise ValueError("display_name is required.")
        category = str(patch.get("category", record.category)).strip()
        if not category:
            raise ValueError("category is required.")
        description = str(patch.get("description", record.description)).strip()
        tags_obj = patch.get("tags", record.tags)
        if not isinstance(tags_obj, list):
            raise ValueError("tags must be a list of strings.")
        tags = sorted({str(tag).strip() for tag in tags_obj if str(tag).strip()})
        protected = bool(patch.get("protected", record.protected))
        return EnvironmentRecord(
            env_id=record.env_id,
            display_name=display_name,
            description=description,
            tags=tags,
            category=category,
            protected=protected,
            last_used_at=record.last_used_at,
            usage_count=record.usage_count,
        )


def _build_confirmation_token(deletable_ids: List[str]) -> str:
    return "CONFIRM_DELETE:" + ",".join(sorted(deletable_ids))


def _parse_iso_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
