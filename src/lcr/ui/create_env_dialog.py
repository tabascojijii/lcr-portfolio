# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QTextEdit, QPushButton, 
    QMessageBox, QFormLayout, QGroupBox, QListWidget, QListWidgetItem,
    QInputDialog, QWidget
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
        self.resize(700, 800)
        
        self.base_images = base_images
        self.initial_config = initial_config
        self.recommended_base_id = recommended_base_id
        self.recommendation_reason = recommendation_reason
        self.result_config = None
        self.apt_warnings = {}  # Loaded metadata for warnings
        
        self._load_apt_warnings()
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
        
        # Base Image with Recommendation Reason
        base_image_layout = QVBoxLayout()
        
        self.base_combo = QComboBox()
        for rule in self.base_images:
            self.base_combo.addItem(rule['name'], rule['id'])
        base_image_layout.addWidget(self.base_combo)
        
        # Recommendation Reason Label (Always visible)
        reason_text = self.recommendation_reason if self.recommendation_reason else "No specific recommendation basis found"
        self.reason_label = QLabel(f"💡 {reason_text}")
        self.reason_label.setStyleSheet(
            "color: #1565c0; "  # Blue color for emphasis
            "font-size: 11px; "
            "font-style: italic; "
            "padding: 4px; "
            "background-color: #e3f2fd; "  # Light blue background
            "border-radius: 3px; "
            "margin-top: 4px;"
        )
        self.reason_label.setWordWrap(True)
        base_image_layout.addWidget(self.reason_label)
        
        form_layout.addRow("Base Image:", base_image_layout)
        
        layout.addLayout(form_layout)
        
        # Reasons & Unresolved Info (if available)
        reasons = self.initial_config.get("_resolution_reasons", {})
        unresolved = self.initial_config.get("_unresolved", [])
        skipped = self.initial_config.get("_skipped_packages", [])
        
        if reasons or unresolved or skipped:
            reason_group = QGroupBox("Resolution Details")
            reason_layout = QVBoxLayout(reason_group)
            
            if unresolved:
                alert = QLabel(f"⚠️ Unresolved / Unconfirmed on PyPI: {', '.join(unresolved)}")
                alert.setStyleSheet("color: red; font-weight: bold;")
                alert.setWordWrap(True)
                reason_layout.addWidget(alert)

            if skipped:
                skip_label = QLabel(f"ℹ️ Skipped (Already in Base): {', '.join(skipped)}")
                skip_label.setStyleSheet("color: gray; font-style: italic;")
                skip_label.setWordWrap(True)
                reason_layout.addWidget(skip_label)
                
            if reasons:
                details_edit = QTextEdit()
                details_edit.setReadOnly(True)
                details_edit.setMaximumHeight(80)
                details_content = "Resolution Map:\n"
                for pkg, r in reasons.items():
                    details_content += f"• {pkg}: {r}\n"
                details_edit.setPlainText(details_content)
                reason_layout.addWidget(details_edit)
            
            layout.addWidget(reason_group)
        
        # Packages
        pkgs_group = QGroupBox("Detected Dependency Gaps", self)
        pkgs_layout = QVBoxLayout(pkgs_group)
        
        # PIP Packages
        pip_header = QHBoxLayout()
        pip_header.addWidget(QLabel("Pip Packages:"))
        pip_add_btn = QPushButton("+ Add")
        pip_add_btn.setFixedSize(60, 25)
        pip_add_btn.clicked.connect(self._add_pip_package)
        pip_header.addWidget(pip_add_btn)
        pip_header.addStretch()
        pkgs_layout.addLayout(pip_header)
        
        self.pip_list = QListWidget()
        pkgs_layout.addWidget(self.pip_list)
        
        # APT Packages
        apt_header = QHBoxLayout()
        apt_header.addWidget(QLabel("Apt Packages:"))
        apt_add_btn = QPushButton("+ Add")
        apt_add_btn.setFixedSize(60, 25)
        apt_add_btn.clicked.connect(self._add_apt_package)
        apt_header.addWidget(apt_add_btn)
        apt_header.addStretch()
        pkgs_layout.addLayout(apt_header)
        
        self.apt_list = QListWidget()
        self.apt_list.setMaximumHeight(120)
        pkgs_layout.addWidget(self.apt_list)
        
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
        target_id = self.recommended_base_id
        
        if target_id:
            idx = self.base_combo.findData(target_id)
            if idx >= 0:
                self.base_combo.setCurrentIndex(idx)
        
        # Populate Lists
        pip_pkgs = self.initial_config.get('pip_packages', [])
        for pkg in pip_pkgs:
            item = QListWidgetItem(pkg)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.pip_list.addItem(item)
            
        apt_pkgs = self.initial_config.get('apt_packages', [])
        for pkg in apt_pkgs:
            item = QListWidgetItem(pkg)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.apt_list.addItem(item)
        
        # Apply Apt warnings if applicable
        self._apply_apt_warnings()
    
    def _load_apt_warnings(self):
        """Load apt compatibility warnings from library.json."""
        try:
            from pathlib import Path
            import json
            mapping_path = Path(__file__).parent.parent / "core" / "detector" / "mappings" / "library.json"
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.apt_warnings = data.get("_meta", {}).get("apt_compatibility", {})
        except Exception as e:
            print(f"[Dialog] Warning: Failed to load apt warnings: {e}")
            self.apt_warnings = {}
    
    def _extract_version_from_image(self, image_str):
        """Extract '3.6', '2.7' etc from image string."""
        import re
        if not image_str:
            return None
        match = re.search(r'(\d+\.\d+)', image_str)
        return match.group(1) if match else None
    
    def _apply_apt_warnings(self):
        """Apply warnings to Apt packages based on base image version."""
        # Get base image
        base_id = self.base_combo.currentData()
        base_rule = next((r for r in self.base_images if r['id'] == base_id), None)
        base_image = base_rule['image'] if base_rule else ""
        
        base_version = self._extract_version_from_image(base_image)
        if not base_version:
            return
        
        # Check each apt package
        for i in range(self.apt_list.count()):
            item = self.apt_list.item(i)
            pkg_name = item.text()
            
            # Check if this apt package has warnings for this version
            if pkg_name in self.apt_warnings:
                incompatible = self.apt_warnings[pkg_name].get("incompatible_with", [])
                if base_version in incompatible:
                    reason = self.apt_warnings[pkg_name].get("reason_ja", "Compatibility warning")
                    item.setToolTip(f"⚠️ {reason}")
                    item.setBackground(QColor("#fff3e0"))  # Orange background
                    print(f"[UI-Warning] Apt package mismatch detected: {pkg_name} on Python {base_version}")

    def _add_pip_package(self):
        """Manually add a pip package."""
        text, ok = QInputDialog.getText(self, "Add Pip Package", "Package Name:")
        if ok and text.strip():
            item = QListWidgetItem(text.strip())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.pip_list.addItem(item)

    def _add_apt_package(self):
        """Manually add an apt package."""
        text, ok = QInputDialog.getText(self, "Add Apt Package", "Package Name:")
        if ok and text.strip():
            item = QListWidgetItem(text.strip())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.apt_list.addItem(item)
            # Apply warnings immediately for newly added package
            self._apply_apt_warnings()

    def get_config(self) -> Optional[Dict]:
        """Return the configured definition."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter an Environment Name.")
            return None
            
        # Get packages from lists (only checked ones)
        pip_pkgs = []
        for i in range(self.pip_list.count()):
            item = self.pip_list.item(i)
            if item.checkState() == Qt.Checked:
                pip_pkgs.append(item.text())

        apt_pkgs = []
        for i in range(self.apt_list.count()):
            item = self.apt_list.item(i)
            if item.checkState() == Qt.Checked:
                apt_pkgs.append(item.text())
        
        # Get base image
        base_id = self.base_combo.currentData()
        base_rule = next((r for r in self.base_images if r['id'] == base_id), None)
        base_image_tag = base_rule['image'] if base_rule else "python:3.10-slim"
        
        config = {
            "tag": name,
            "base_image": base_image_tag,
            "pip_packages": pip_pkgs,
            "apt_packages": apt_pkgs,
            "env_vars": {"PYTHONUNBUFFERED": "1"}, 
            "run_commands": []
        }
        return config

    def accept(self):
        """Validate before accepting."""
        result = self.get_config()
        if result:
            pip_pkgs = result.get('pip_packages', [])
            apt_pkgs = result.get('apt_packages', [])
            base_image = result.get('base_image', '')

            # --- Strategy 0: Legacy Version Pinning (New) ---
            # If base image is Python 3.6, apply known version pins from library.json
            if "3.6" in base_image:
                try:
                    import json
                    from pathlib import Path
                    # Load library.json relative to this file's known location in src/lcr/ui -> src/lcr/core/detector/mappings
                    # Or reuse the one from core if available. But here we load it directly to be safe.
                    # Assuming we are in src/lcr/ui/create_env_dialog.py
                    # library.json is in ../core/detector/mappings/library.json
                    mapping_path = Path(__file__).parent.parent / "core" / "detector" / "mappings" / "library.json"
                    if mapping_path.exists():
                        with open(mapping_path, 'r', encoding='utf-8') as f:
                            lib_data = json.load(f)
                            legacy_pins = lib_data.get("_meta", {}).get("legacy_versions", {}).get("3.6", {})
                            
                            # Apply pins
                            new_pip = []
                            for pkg in pip_pkgs:
                                # Strip existing version info if any (though usually just name)
                                pkg_name = pkg.split('==')[0].split('>=')[0].split('<=')[0]
                                if pkg_name in legacy_pins:
                                    pin = legacy_pins[pkg_name]
                                    new_pkg = f"{pkg_name}{pin}"
                                    new_pip.append(new_pkg)
                                else:
                                    new_pip.append(pkg)
                            
                            result['pip_packages'] = new_pip
                            pip_pkgs = new_pip # Update reference
                except Exception as e:
                    print(f"Warning: Failed to apply legacy pins: {e}")

            # --- Strategy 1: Dependency Cleanup ---
            # If python3-opencv (Apt) is selected, explicit build tools are likely unnecessary/redundant.
            if "python3-opencv" in apt_pkgs:
                unnecessary = {'build-essential', 'cmake'}
                # Filter them out
                result['apt_packages'] = [p for p in apt_pkgs if p not in unnecessary]
                apt_pkgs = result['apt_packages'] # Update reference
                
                # Log or subtle notice could go here, but silent optimization is preferred by user request ("automatically exclude")

            # --- Strategy 2: Build Time Warning ---
            # If using pip opencv, warn about build time on legacy systems.
            opencv_pip = [p for p in pip_pkgs if "opencv" in p and "python" in p]
            if opencv_pip:
                msg = ("<b>Run-Time Warning: Source Build Likely</b><br><br>"
                       "You have selected <code>opencv-python</code> via pip.<br>"
                       "On legacy environments (e.g. Python 3.6), this often triggers a source build "
                       "that can take <b>20-40 minutes</b>.<br><br>"
                       "<b>Recommendation:</b> Use <code>python3-opencv</code> (Apt) instead.")
                reply = QMessageBox.warning(self, "Build Time Warning", msg, 
                                            QMessageBox.Ok | QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return

            # --- Strategy 3: Auto-Add Build Tools ---
            # Existing logic, but skipped if we are in "Apt OpenCV" mode (assuming clean environment)
            # or if we just removed them. 
            if pip_pkgs and "python3-opencv" not in apt_pkgs:
                needed_tools = {'build-essential', 'cmake', 'python3-dev'}
                current_apt = set(apt_pkgs)
                missing = needed_tools - current_apt
                
                if missing:
                    # Auto-add them
                    msg = (f"Detected pip packages ({len(pip_pkgs)} items). \n"
                           f"To ensure successful build, I am adding the following build tools to Apt packages:\n"
                           f"{', '.join(missing)}")
                    
                    QMessageBox.information(self, "Apt-First Assist", msg)
                    
                    # Add to config
                    result['apt_packages'].extend(list(missing))
                    
            self.result_config = result
            super().accept()
