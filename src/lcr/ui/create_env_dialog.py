# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QTextEdit, QPushButton, 
    QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt
from lcr.core.container.types import ImageRule

class EnvironmentCreationDialog(QDialog):
    """
    Dialog for creating a new custom environment definition.
    Allows user to name the environment via Tag, select a base image, 
    and customize installed packages.
    """
    
    def __init__(self, parent=None, base_images: List[ImageRule] = [], initial_config: Dict = {}, 
                 recommended_base_id: Optional[str] = None, recommendation_reason: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Runtime Environment")
        self.resize(600, 700) # Slightly larger
        
        self.base_images = base_images
        self.initial_config = initial_config
        self.recommended_base_id = recommended_base_id
        self.recommendation_reason = recommendation_reason
        self.result_config = None
        
        self._setup_ui()
        self._populate_fields()
        
    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Synthesize Custom Environment")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Form
        form_layout = QFormLayout()
        
        # Name / Tag
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. my-experiment-env")
        form_layout.addRow("Environment Name:", self.name_input)
        
        # Base Image
        self.base_combo = QComboBox()
        for rule in self.base_images:
            self.base_combo.addItem(rule['name'], rule['id'])
        form_layout.addRow("Base Image:", self.base_combo)
        
        # Recommendation Label
        if self.recommendation_reason:
            rec_label = QLabel(f"ℹ️ {self.recommendation_reason}")
            rec_label.setStyleSheet("color: #2e7d32; font-size: 11px; margin-left: 5px;")
            rec_label.setWordWrap(True)
            form_layout.addRow("", rec_label)
        
        layout.addLayout(form_layout)
        
        # Reasons & Unresolved Info (if available)
        reasons = self.initial_config.get("_resolution_reasons", {})
        unresolved = self.initial_config.get("_unresolved", [])
        
        if reasons or unresolved:
            reason_group = QGroupBox("Resolution Details")
            reason_layout = QVBoxLayout(reason_group)
            
            if unresolved:
                alert = QLabel(f"⚠️ Unresolved / Unconfirmed on PyPI: {', '.join(unresolved)}")
                alert.setStyleSheet("color: red; font-weight: bold;")
                alert.setWordWrap(True)
                reason_layout.addWidget(alert)
                
            if reasons:
                details_edit = QTextEdit()
                details_edit.setReadOnly(True)
                details_edit.setMaximumHeight(100)
                details_content = "Resolution Map:\n"
                for pkg, r in reasons.items():
                    details_content += f"• {pkg}: {r}\n"
                details_edit.setPlainText(details_content)
                reason_layout.addWidget(details_edit)
            
            layout.addWidget(reason_group)
        
        # Packages
        pkgs_group = QGroupBox("Detected Dependency Gaps", self)
        pkgs_layout = QVBoxLayout(pkgs_group)
        
        pkgs_layout.addWidget(QLabel("Pip Packages (one per line):"))
        self.pip_edit = QTextEdit()
        pkgs_layout.addWidget(self.pip_edit)
        
        pkgs_layout.addWidget(QLabel("Apt Packages (one per line):"))
        self.apt_edit = QTextEdit()
        self.apt_edit.setMaximumHeight(80)
        pkgs_layout.addWidget(self.apt_edit)
        
        layout.addWidget(pkgs_group)
        
        # Disclaimer
        note = QLabel("Note: 'Save & Build' will save this definition to 'definitions/' "
                      "and immediately start building the container image.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        layout.addWidget(note)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save & Build")
        self.save_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def _populate_fields(self):
        """Populate fields with initial config."""
        # Set base image
        # Priority: Recommended ID -> Config Base (if mapped to ID) -> First
        
        target_id = self.recommended_base_id
        
        # If no recommendation, try to reverse-lookup from config base image string?
        # But 'base_image' in config is a docker tag (e.g. python:3.6), 'id' is internal rule id.
        # So we really rely on recommended_base_id passed in.
        
        if target_id:
            idx = self.base_combo.findData(target_id)
            if idx >= 0:
                self.base_combo.setCurrentIndex(idx)
        else:
            # Fallback default
            pass # Keep 0 index
        
        # Set packages
        
        # Set packages
        pip_pkgs = self.initial_config.get('pip_packages', [])
        self.pip_edit.setPlainText('\n'.join(pip_pkgs))
        
        apt_pkgs = self.initial_config.get('apt_packages', [])
        self.apt_edit.setPlainText('\n'.join(apt_pkgs))

    def get_config(self) -> Optional[Dict]:
        """Return the configured definition."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter an Environment Name.")
            return None
            
        # Get packages
        pip_pkgs = [p.strip() for p in self.pip_edit.toPlainText().split('\n') if p.strip()]
        apt_pkgs = [p.strip() for p in self.apt_edit.toPlainText().split('\n') if p.strip()]
        
        # Get base image
        base_id = self.base_combo.currentData()
        base_rule = next((r for r in self.base_images if r['id'] == base_id), None)
        base_image_tag = base_rule['image'] if base_rule else "python:3.10-slim"
        
        config = {
            "tag": name,
            "base_image": base_image_tag,
            "pip_packages": sip_pkgs if 'sip_pkgs' in locals() else pip_pkgs, # typo fix
            "pip_packages": pip_pkgs,
            "apt_packages": apt_pkgs,
            "env_vars": {"PYTHONUNBUFFERED": "1"}, # Default good practice
            "run_commands": []
        }
        return config

    def accept(self):
        """Validate before accepting."""
        result = self.get_config()
        if result:
            self.result_config = result
            # Check for name collision (simple check if we had access to manager, 
            # but main window logic handles the overwrite confirmation usually)
            super().accept()
