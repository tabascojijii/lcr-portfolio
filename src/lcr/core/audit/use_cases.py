from pathlib import Path


class CollectAuditMetadataUseCase:
    """Collect audit metadata using abstract dependencies."""

    def __init__(self, history_manager, audit_metadata_service):
        self.history_manager = history_manager
        self.audit_metadata_service = audit_metadata_service

    def execute(
        self,
        image_name: str,
        script_path: str,
        param_payload=None,
        input_files=None,
        output_files=None,
        log_path=None,
        required_imports=None,
        environment_capability=None,
        mismatch_result=None,
        guard_state="unknown",
        fail_on_incomplete_audit=False,
    ):
        script_rel = self.history_manager.to_relative_path(script_path)
        input_files = input_files or []
        output_files = output_files or []
        input_rel = [self.history_manager.to_relative_path(p) for p in input_files]
        output_rel = [self.history_manager.to_relative_path(p) for p in output_files]
        log_rel = self.history_manager.to_relative_path(log_path) if log_path else None
        metadata = self.audit_metadata_service.collect(
            image_name,
            script_path,
            script_rel,
            param_payload=param_payload or {},
            input_files=input_files,
            input_files_rel=input_rel,
            output_files=output_files,
            output_files_rel=output_rel,
            log_path=log_path,
            log_path_rel=log_rel,
            required_imports=required_imports or [],
            environment_capability=environment_capability or {},
            mismatch_result=mismatch_result or {},
            guard_state=guard_state,
        )
        if fail_on_incomplete_audit:
            self._ensure_required_audit_fields(metadata)
        return metadata

    def _ensure_required_audit_fields(self, metadata):
        required_keys = (
            "operation_type",
            "timestamp",
            "targets",
            "result",
            "released_size",
            "reason",
            "image_digest",
            "container_image_digest",
            "git_commit_hash",
            "script_path_rel",
            "script_sha256",
            "required_imports",
            "environment_capability",
            "mismatch_result",
            "guard_triggered",
            "parameter_sha256",
            "input_sha256",
            "output_sha256",
            "log_sha256",
            "hashes",
        )
        missing = [key for key in required_keys if key not in metadata]
        if missing:
            raise ValueError(f"Incomplete audit metadata: missing keys: {', '.join(missing)}")

        unavailable = []
        for key in ("image_digest", "git_commit_hash", "log_sha256"):
            value = str(metadata.get(key, "")).strip().lower()
            if not value or value == "unavailable" or value.startswith("unavailable:"):
                unavailable.append(key)
        if unavailable:
            raise ValueError(f"Incomplete audit metadata: unavailable fields: {', '.join(unavailable)}")

        hashes = metadata.get("hashes") or {}
        hash_keys = ("all_input_files", "all_output_files", "all_parameter_files", "audit_log_record")
        missing_hash_keys = [k for k in hash_keys if k not in hashes]
        if missing_hash_keys:
            raise ValueError(f"Incomplete audit metadata: missing hashes keys: {', '.join(missing_hash_keys)}")


class PrepareAuditMetadataUseCase:
    """Application-layer orchestration for audit metadata collection."""

    def __init__(self, collect_use_case, log_path_provider):
        self.collect_use_case = collect_use_case
        self.log_path_provider = log_path_provider

    def execute(self, last_run_context, output_dir, exit_code):
        output_files = self._collect_output_files(output_dir) if output_dir else []
        log_path = str(self.log_path_provider("lcr_debug.log"))
        return self.collect_use_case.execute(
            last_run_context.get("image_name", ""),
            last_run_context.get("script_path", ""),
            param_payload=last_run_context.get("param_payload", {}),
            input_files=last_run_context.get("input_files", []),
            output_files=output_files if exit_code == 0 else [],
            log_path=log_path if Path(log_path).exists() else None,
        )

    def _collect_output_files(self, output_dir):
        out_dir = Path(output_dir)
        if not out_dir.exists():
            return []
        return [str(path) for path in out_dir.rglob("*") if path.is_file()]
