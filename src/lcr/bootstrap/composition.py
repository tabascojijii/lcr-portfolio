from lcr.core.audit import AuditMetadataService
from lcr.core.audit.use_cases import CollectAuditMetadataUseCase, PrepareAuditMetadataUseCase
from lcr.core.container.manager import ContainerManager
from lcr.core.container.use_cases import (
    EnvironmentBuildPreparationUseCase,
    EnvironmentDraftUseCase,
    RuntimeExecutionPreparationUseCase,
)
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.detector.use_cases import CodeAnalysisUseCase
from lcr.core.history.manager import HistoryManager
from lcr.core.history.use_cases import SaveExecutionHistoryUseCase
from lcr.core.results.use_cases import LoadResultArtifactsUseCase
from lcr.utils.path_helper import get_log_path


def build_main_window_dependencies():
    analyzer = CodeAnalyzer()
    container_manager = ContainerManager()
    history_manager = HistoryManager()
    audit_metadata_service = AuditMetadataService()
    collect_audit_metadata_use_case = CollectAuditMetadataUseCase(
        history_manager, audit_metadata_service
    )
    return {
        "analyzer": analyzer,
        "container_manager": container_manager,
        "history_manager": history_manager,
        "audit_metadata_service": audit_metadata_service,
        "runtime_use_case": RuntimeExecutionPreparationUseCase(),
        "environment_draft_use_case": EnvironmentDraftUseCase(analyzer, container_manager),
        "environment_build_preparation_use_case": EnvironmentBuildPreparationUseCase(container_manager),
        "save_history_use_case": SaveExecutionHistoryUseCase(history_manager),
        "code_analysis_use_case": CodeAnalysisUseCase(analyzer, container_manager),
        "collect_audit_metadata_use_case": collect_audit_metadata_use_case,
        "prepare_audit_metadata_use_case": PrepareAuditMetadataUseCase(
            collect_audit_metadata_use_case, get_log_path
        ),
        "load_result_artifacts_use_case": LoadResultArtifactsUseCase(),
    }
