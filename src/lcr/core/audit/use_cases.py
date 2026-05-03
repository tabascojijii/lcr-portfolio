class CollectAuditMetadataUseCase:
    """Collect audit metadata using abstract dependencies."""

    def __init__(self, history_manager, audit_metadata_service):
        self.history_manager = history_manager
        self.audit_metadata_service = audit_metadata_service

    def execute(self, image_name: str, script_path: str):
        script_rel = self.history_manager.to_relative_path(script_path)
        return self.audit_metadata_service.collect(image_name, script_path, script_rel)
