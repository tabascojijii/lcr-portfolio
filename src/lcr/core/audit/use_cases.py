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
    ):
        script_rel = self.history_manager.to_relative_path(script_path)
        input_files = input_files or []
        output_files = output_files or []
        input_rel = [self.history_manager.to_relative_path(p) for p in input_files]
        output_rel = [self.history_manager.to_relative_path(p) for p in output_files]
        log_rel = self.history_manager.to_relative_path(log_path) if log_path else None
        return self.audit_metadata_service.collect(
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
