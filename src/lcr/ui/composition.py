from lcr.core.audit import AuditMetadataService
from lcr.core.container.manager import ContainerManager
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.history.manager import HistoryManager


def build_main_window_dependencies():
    return {
        "analyzer": CodeAnalyzer(),
        "container_manager": ContainerManager(),
        "history_manager": HistoryManager(),
        "audit_metadata_service": AuditMetadataService(),
    }
