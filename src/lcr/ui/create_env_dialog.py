# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QTextEdit, QPushButton, 
    QMessageBox, QFormLayout, QGroupBox, QListWidget, QListWidgetItem,
    QInputDialog, QWidget, QProgressBar
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QColor

from lcr.core.container.types import ImageRule
from lcr.core.container.manager import ContainerManager
from lcr.core.container.generator import save_definition, generate_dockerfile
from lcr.ui.workers import BuildWorker

class EnvironmentCreationDialog(QDialog):
    """
    Dialog for creating a new custom environment definition.
    Allows user to name the environment via Tag, select a base image, 
    and customize installed packages.
    """
    
    def __init__(self, parent=None, container_manager: ContainerManager = None, base_images: List[ImageRule] = [], initial_config: Dict = {}, 
                 recommended_base_id: Optional[str] = None, recommendation_reason: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Runtime Environment")
        self.resize(700, 850)
        
        self.container_manager = container_manager
        self.base_images = base_images
        self.initial_config = initial_config
        self.recommended_base_id = recommended_base_id
        self.recommendation_reason = recommendation_reason
        self.result_config = None
        self.apt_warnings = {}  # Loaded metadata for warnings
        
        # Build State
        self.worker: Optional[BuildWorker] = None
        self.is_building = False
        self.current_def_id = None  # Track ID for rollback
        
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
        
        # [REQ-1] Log Console (Initially Hidden)
        self.log_group = QGroupBox("Build Progress")
        self.log_group.setVisible(False)
        log_layout = QVBoxLayout(self.log_group)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: black; color: white; font-family: Consolas; font-size: 10pt;")
        self.log_console.setMinimumHeight(200)
        log_layout.addWidget(self.log_console)
        
        layout.addWidget(self.log_group)

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
        """
        Validate and start build process inside dialog window.
        Overrides standard accept to prevent closing.
        """
        # If already building, do nothing (button should be disabled anyway)
        if self.is_building:
            return

        result = self.get_config()
        if not result:
            return

        # --- Validation & Pre-processing (Copy of original logic) ---
        pip_pkgs = result.get('pip_packages', [])
        apt_pkgs = result.get('apt_packages', [])
        base_image = result.get('base_image', '')

        # Legacy Pins (3.6)
        if "3.6" in base_image:
            try:
                import json
                from pathlib import Path
                mapping_path = Path(__file__).parent.parent / "core" / "detector" / "mappings" / "library.json"
                if mapping_path.exists():
                    with open(mapping_path, 'r', encoding='utf-8') as f:
                        lib_data = json.load(f)
                        legacy_pins = lib_data.get("_meta", {}).get("legacy_versions", {}).get("3.6", {})
                        new_pip = []
                        for pkg in pip_pkgs:
                            pkg_name = pkg.split('==')[0].split('>=')[0].split('<=')[0]
                            if pkg_name in legacy_pins:
                                pin = legacy_pins[pkg_name]
                                new_pip.append(f"{pkg_name}{pin}")
                            else:
                                new_pip.append(pkg)
                        result['pip_packages'] = new_pip
                        pip_pkgs = new_pip
            except Exception as e:
                print(f"Warning: Failed to apply legacy pins: {e}")

        # Opt Dependency Cleanup
        if "python3-opencv" in apt_pkgs:
            unnecessary = {'build-essential', 'cmake'}
            result['apt_packages'] = [p for p in apt_pkgs if p not in unnecessary]
            apt_pkgs = result['apt_packages']

        # Warnings
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

        # Auto-Add Tools
        if pip_pkgs and "python3-opencv" not in apt_pkgs:
            needed_tools = {'build-essential', 'cmake', 'python3-dev'}
            current_apt = set(apt_pkgs)
            missing = needed_tools - current_apt
            if missing:
                msg = (f"Detected pip packages ({len(pip_pkgs)} items). \n"
                       f"To ensure successful build, I am adding the following build tools to Apt packages:\n"
                       f"{', '.join(missing)}")
                QMessageBox.information(self, "Apt-First Assist", msg)
                result['apt_packages'].extend(list(missing))
        
        self.result_config = result
        
        # --- Start Build Sequence ---
        self._start_build(result)

    def _start_build(self, config):
        """Initialize build process with Worker."""
        tag = config['tag']
        self.current_def_id = tag # Assuming tag is ID for now
        
        try:
            # 1. Provisional Save (Transaction Start)
            # Use provisional save if manager supports it, or standard save with manual rollback
            if self.container_manager:
                 # Note: manager.save_definition_provisional not fully implemented in previous context
                 # user said "Create newly generated image tag" etc. 
                 # We will use save_definition from generator but track it manually for rollback
                 json_path = save_definition(config, tag)
                 
                 # Register transaction start in manager if needed, or just track locally
                 # manager.save_definition_provisional(config) # If this existed
                 pass
            else:
                 json_path = save_definition(config, tag)
            
            self.log_console.clear()
            self.log_console.append(f"[Generator] Definition saved to {json_path.name}")
            
            # 2. Generate Dockerfile
            tag, dockerfile_path = generate_dockerfile(str(json_path))
            
            # 3. Get Build Command
            if self.container_manager:
                build_args = self.container_manager.get_build_command(dockerfile_path, tag)
            else:
                # Fallback if manager missing (unlikely)
                raise ValueError("ContainerManager not initialized")

            # 4. Prepare UI
            self.is_building = True
            self.setCursor(Qt.WaitCursor)
            
            # Lock UI
            self.name_input.setEnabled(False)
            self.base_combo.setEnabled(False)
            self.pip_list.setEnabled(False)
            self.apt_list.setEnabled(False)
            self.save_btn.setEnabled(False) # Disable Save
            self.cancel_btn.setText("Stop Build") # Change Cancel to Stop
            self.cancel_btn.setStyleSheet("color: red; font-weight: bold;")
            
            # Show Console
            self.log_group.setVisible(True)
            self.log_console.append(f"\n[Builder] Starting build for '{tag}'...")
            
            # 5. Start Worker
            self.worker = BuildWorker(build_args, tag)
            self.worker.log_received.connect(self._append_log)
            self.worker.build_finished.connect(self._on_build_finished)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Start Error", str(e))
            self._reset_ui_state()

    @Slot(str)
    def _append_log(self, text):
        """Append log text from worker."""
        # [REQ-4] Buffer Limit
        self.log_console.append(text)
        if self.log_console.document().blockCount() > 1000:
            cursor = self.log_console.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100) # Remove oldest 100 lines
            cursor.removeSelectedText()
        
        # Auto-scroll
        self.log_console.ensureCursorVisible()

    @Slot(int, str)
    def _on_build_finished(self, exit_code, tag):
        """Handle build completion."""
        self.setCursor(Qt.ArrowCursor)
        self.is_building = False
        
        if exit_code == 0:
            # Success
            self.log_console.append(f"\n[Builder] Build Success! (Tag: {tag})")
            
            # Commit Transaction
            if self.container_manager:
                self.container_manager.commit_definition(tag)
            
            QMessageBox.information(self, "Build Complete", f"Environment '{tag}' created successfully.")
            
            # Close dialog returning Success
            super().accept()
            
        else:
            # Failure
            self.log_console.append(f"\n[Builder] Build Failed (Exit Code: {exit_code})")
            
            # Rollback
            if self.container_manager and exit_code != -1: # -1 is manual cancel, handled in reject
                 # For actual failures, we rollback definition to prevent broken usage
                 self.container_manager.rollback_definition(tag)
                 self.log_console.append(f"[Transaction] Definition rolled back.")
            
            # Keep Dialog Open, Enable Interaction
            self.cancel_btn.setText("Close")
            self.cancel_btn.setStyleSheet("")
            self.save_btn.setEnabled(True) # Allow retry? Or maybe user wants to edit config
            
            # Unlock inputs for editing
            self.name_input.setEnabled(True)
            self.base_combo.setEnabled(True)
            self.pip_list.setEnabled(True)
            self.apt_list.setEnabled(True)
            
            QMessageBox.warning(self, "Build Failed", 
                                "Docker build failed. Check logs below for details.\n"
                                "You can modify settings and try again.")

    def reject(self):
        """Handle Cancel / Close events."""
        if self.is_building and self.worker:
            # [REQ-3] Stop & Rollback
            ans = QMessageBox.question(self, "Stop Build?", 
                                      "Build is in progress. Stopping it will discard changes.\nContinue?",
                                      QMessageBox.Yes | QMessageBox.No)
            
            if ans == QMessageBox.Yes:
                self.log_console.append("\n[User] Stopping build...")
                self.worker.stop()
                self.worker.wait() # Wait for thread to finish cleanup
                
                # Rollback
                if self.container_manager and self.current_def_id:
                     self.container_manager.rollback_definition(self.current_def_id)
                
                super().reject()
        else:
            # Normal close
            super().reject()

    def _reset_ui_state(self):
        """Reset UI to non-building state."""
        self.setCursor(Qt.ArrowCursor)
        self.is_building = False
        self.name_input.setEnabled(True)
        self.base_combo.setEnabled(True)
        self.pip_list.setEnabled(True)
        self.apt_list.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self.cancel_btn.setStyleSheet("")
