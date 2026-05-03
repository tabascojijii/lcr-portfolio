import datetime
import uuid
from typing import Dict

from lcr.core.history.types import ExecutionHistory


class SaveExecutionHistoryUseCase:
    """Use case for constructing and saving execution history records."""

    def __init__(self, history_manager):
        self.history_manager = history_manager

    def save(
        self,
        script_path: str,
        runtime_name: str,
        output_dir: str,
        exit_code: int,
        selection_mode: str,
        selection_reason: str,
        image_tag: str,
    ) -> ExecutionHistory:
        record: ExecutionHistory = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "script_path": script_path,
            "runtime_name": runtime_name,
            "image_tag": image_tag,
            "output_dir": output_dir,
            "status": "success" if exit_code == 0 else "failed",
            "selection_mode": selection_mode,
            "selection_reason": selection_reason,
        }
        self.history_manager.save_record(record)
        return record
