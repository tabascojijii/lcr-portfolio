from typing import Any, Dict, List, Optional

from lcr.ui.create_env_dialog import EnvironmentCreationDialog


class QtEnvironmentDialogAdapter:
    """Qt adapter to open environment creation dialog via a UI port."""

    def __init__(self, build_use_case: Any):
        self._build_use_case = build_use_case

    def open_creation_dialog(
        self,
        *,
        parent: Any,
        base_images: List[Dict[str, Any]],
        initial_config: Dict[str, Any],
        recommended_base_id: str,
        recommendation_reason: str,
    ) -> Optional[Dict[str, Any]]:
        dialog = EnvironmentCreationDialog(
            parent=parent,
            base_images=base_images,
            initial_config=initial_config,
            recommended_base_id=recommended_base_id,
            recommendation_reason=recommendation_reason,
            build_use_case=self._build_use_case,
        )
        if dialog.exec():
            return dialog.result_config
        return None
