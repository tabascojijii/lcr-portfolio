# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Main Window for Legacy Code Reviver (LCR) GUI.

This module implements the primary user interface using PySide6,
connecting the CodeAnalyzer, ContainerManager, and ContainerWorker.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QTextEdit,
    QGroupBox, QFileDialog, QMessageBox, QApplication, QTabWidget,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem, QComboBox
)
from PySide6.QtGui import QFont, QColor, QPixmap, QDesktopServices
from PySide6.QtCore import Qt, Slot, QUrl

from lcr.core.container.use_cases import (
    EnvironmentBuildPreparationUseCase,
    EnvironmentDraftUseCase,
    RuntimeExecutionPreparationUseCase,
)
from lcr.core.history.use_cases import SaveExecutionHistoryUseCase
from lcr.core.detector.use_cases import CodeAnalysisUseCase
from lcr.core.audit.use_cases import CollectAuditMetadataUseCase, PrepareAuditMetadataUseCase
from lcr.core.results.use_cases import LoadResultArtifactsUseCase
from lcr.utils.path_helper import get_log_path
from lcr.ui.create_env_dialog import EnvironmentCreationDialog
from lcr.ui.workers import ContainerWorker
from lcr.ui.ports import AnalyzerPort, AuditMetadataPort, ContainerManagerPort, HistoryManagerPort
from lcr.ui.composition import build_main_window_dependencies


class MainWindow(QMainWindow):
    """Main window of the application."""

    def __init__(
        self,
        analyzer: Optional[AnalyzerPort] = None,
        container_manager: Optional[ContainerManagerPort] = None,
        history_manager: Optional[HistoryManagerPort] = None,
        audit_metadata_service: Optional[AuditMetadataPort] = None,
    ):
        super().__init__()
        self.setWindowTitle("Legacy Code Reviver")
        self.resize(1200, 800)

        deps = {}
        if not (analyzer and container_manager and history_manager and audit_metadata_service):
            deps = build_main_window_dependencies()

        # backend components
        self.analyzer = analyzer or deps["analyzer"]
        self.container_manager = container_manager or deps["container_manager"]
        if not self.container_manager:
            raise RuntimeError("Failed to initialize ContainerManager")
        self.history_manager = history_manager or deps["history_manager"]
        self.runtime_use_case = RuntimeExecutionPreparationUseCase()
        self.environment_draft_use_case = EnvironmentDraftUseCase(self.analyzer, self.container_manager)
        self.environment_build_preparation_use_case = EnvironmentBuildPreparationUseCase(self.container_manager)
        self.save_history_use_case = SaveExecutionHistoryUseCase(self.history_manager)
        self.audit_metadata_service = audit_metadata_service or deps["audit_metadata_service"]
        self.code_analysis_use_case = CodeAnalysisUseCase(self.analyzer, self.container_manager)
        self.collect_audit_metadata_use_case = CollectAuditMetadataUseCase(
            self.history_manager, self.audit_metadata_service
        )
        self.prepare_audit_metadata_use_case = PrepareAuditMetadataUseCase(
            self.collect_audit_metadata_use_case, get_log_path
        )
        self.load_result_artifacts_use_case = LoadResultArtifactsUseCase()
        self.worker = None
        self.current_output_dir = None
        self.selection_mode = 'Auto'
        self._last_run_context = {}


        # setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Initialize all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Splitter to divide Editor (Left) and Control (Right)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Pane: Editor Area ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Script Selection
        script_select_layout = QHBoxLayout()
        self.script_path_edit = QLineEdit()
        self.script_path_edit.setPlaceholderText("Path to legacy python script...")
        self.script_path_edit.setReadOnly(True)
        
        self.select_script_btn = QPushButton("Select Legacy Script")
        self.select_script_btn.clicked.connect(self._select_script)
        
        script_select_layout.addWidget(QLabel("Script:"))
        script_select_layout.addWidget(self.script_path_edit)
        script_select_layout.addWidget(self.select_script_btn)
        
        left_layout.addLayout(script_select_layout)

        # Code Editor
        self.code_editor = QPlainTextEdit()
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.code_editor.setFont(font)
        
        left_layout.addWidget(QLabel("Code Preview:"))
        left_layout.addWidget(self.code_editor)

        splitter.addWidget(left_widget)

        # --- Right Pane: Control/Monitor Area ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Data Selection
        data_select_layout = QHBoxLayout()
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setPlaceholderText("Input data directory (mounts to /data)...")
        
        self.select_data_btn = QPushButton("Browse...")
        self.select_data_btn.clicked.connect(self._select_data_dir)
        
        data_select_layout.addWidget(QLabel("Input Data:"))
        data_select_layout.addWidget(self.data_dir_edit)
        data_select_layout.addWidget(self.select_data_btn)
        
        right_layout.addLayout(data_select_layout)

        # Output Selection
        output_select_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output directory (Optional, defaults to project results)...")
        
        self.select_output_btn = QPushButton("Browse...")
        self.select_output_btn.clicked.connect(self._select_output_dir)
        
        output_select_layout.addWidget(QLabel("Output Dir:"))
        output_select_layout.addWidget(self.output_dir_edit)
        output_select_layout.addWidget(self.select_output_btn)
        
        right_layout.addLayout(output_select_layout)

        # Environment Info
        self.env_group = QGroupBox("Detected Environment Info")
        env_layout = QVBoxLayout()
        self.version_label = QLabel("Detected Version: -")
        self.libraries_label = QLabel("Detected Libraries: -")
        self.sloc_label = QLabel("SLOC: -")
        self.ratio_label = QLabel("Comment Ratio: -")
        
        env_layout.addWidget(self.version_label)
        env_layout.addWidget(self.libraries_label)
        env_layout.addWidget(self.sloc_label)
        env_layout.addWidget(self.ratio_label)
        
        # Runtime Selection Combo
        env_layout.addWidget(QLabel("Runtime Environment:"))
        self.runtime_combo = QComboBox()
        self.runtime_combo.setToolTip("Select the Docker environment for execution.")
        self.runtime_combo.activated.connect(self._on_runtime_combo_activated)
        
        # Populate initially
        self._refresh_env_list()
        
        env_combo_layout = QHBoxLayout()
        env_combo_layout.addWidget(self.runtime_combo)
        
        # New Env Button
        self.create_env_btn = QPushButton("New")
        self.create_env_btn.setToolTip("Synthesize a new runtime environment")
        self.create_env_btn.setMaximumWidth(50)
        self.create_env_btn.clicked.connect(self._show_create_env_dialog)
        env_combo_layout.addWidget(self.create_env_btn)
        
        env_layout.addLayout(env_combo_layout)
        
        # Runtime Info Label (Dynamic)
        self.runtime_info_label = QLabel("")
        self.runtime_info_label.setWordWrap(True)
        self.runtime_info_label.setStyleSheet("color: #555;")
        env_layout.addWidget(self.runtime_info_label)

        # Mode Label
        self.mode_label = QLabel("Mode: Auto")
        self.mode_label.setStyleSheet("color: gray; font-style: italic;")
        env_layout.addWidget(self.mode_label)

        self.env_group.setLayout(env_layout)
        
        right_layout.addWidget(self.env_group)

        # Tabs: Console and Results
        self.tabs = QTabWidget()
        
        # Tab 1: Console
        self.console_tab = QWidget()
        console_layout = QVBoxLayout(self.console_tab)
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
        console_layout.addWidget(self.console_log)
        self.tabs.addTab(self.console_tab, "Console Logs")
        
        # Tab 2: Results Preview
        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout(self.results_tab)
        
        # Header (Timestamp + Open Folder)
        res_header = QHBoxLayout()
        self.res_timestamp_label = QLabel("Run Timestamp: -")
        self.res_timestamp_label.setStyleSheet("font-weight: bold;")
        self.open_res_btn = QPushButton("Open Result Folder")
        self.open_res_btn.setEnabled(False)
        self.open_res_btn.clicked.connect(self._open_result_folder)
        
        res_header.addWidget(self.res_timestamp_label)
        res_header.addStretch()
        res_header.addWidget(self.open_res_btn)
        self.results_layout.addLayout(res_header)
        
        # Content Areas (Scrollable)
        self.res_scroll = QScrollArea()
        self.res_scroll.setWidgetResizable(True)
        self.res_content_widget = QWidget()
        self.res_content_layout = QVBoxLayout(self.res_content_widget)
        self.res_scroll.setWidget(self.res_content_widget)
        
        self.results_layout.addWidget(self.res_scroll)
        self.tabs.addTab(self.results_tab, "Results Preview")
        
        # Tab 3: History
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemDoubleClicked.connect(self._on_history_double_clicked)
        history_layout.addWidget(self.history_list)
        
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self._refresh_history_list)
        history_layout.addWidget(refresh_btn)
        
        self.tabs.addTab(self.history_tab, "History")
        
        # Initial Load
        self._refresh_history_list()
        
        right_layout.addWidget(self.tabs)

        # Action Buttons
        actions_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self._run_analysis)
        
        self.run_btn = QPushButton("Run in Container")
        self.run_btn.clicked.connect(self._run_container)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_container)
        
        actions_layout.addWidget(self.analyze_btn)
        actions_layout.addWidget(self.run_btn)
        actions_layout.addWidget(self.stop_btn)
        
        right_layout.addLayout(actions_layout)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        right_layout.addWidget(self.status_label)

        # Add right pane to splitter
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])

    def _refresh_env_list(self):
        """Reload definitions and update runtime combo dropdown."""
        self.runtime_combo.clear()
        rules = self.container_manager.get_available_runtimes()
        for i, rule in enumerate(rules):
            self.runtime_combo.addItem(rule['name'])
            # Store full rule in UserRole
            self.runtime_combo.setItemData(i, rule, Qt.UserRole)
            # Tooltip: Base Image
            desc = rule.get('description', f"Image: {rule['image']}")
            self.runtime_combo.setItemData(i, desc, Qt.ToolTipRole)
        print(f"[UI] Environment list refreshed. {len(rules)} items found.")

    def _populate_runtime_combo(self):
        """Compatibility alias for _refresh_env_list."""
        self._refresh_env_list()

    @Slot(int)
    def _on_runtime_combo_activated(self, index):
        """Handle manual user selection."""
        # Guard: Check valid index
        if index < 0:
            return
            
        # Retrieve rule data
        rule = self.runtime_combo.itemData(index, Qt.UserRole)
        if not rule:
            self.console_log.append("[Warning] Invalid runtime selection - no data found.")
            return
        
        # Update state
        self.selection_mode = 'Manual'
        
        # Update UI display
        self._update_runtime_display(rule, is_manual=True)

    def _update_runtime_display(self, rule, is_manual=False):
        """Update runtime environment display with selected rule info.
        
        Args:
            rule: ImageRule dictionary with runtime information
            is_manual: True if manual selection, False if auto-detected
        """
        # Update Runtime Info Label
        display_text = f"Image: {rule['image']}\nTag: {rule.get('tag', 'latest')}"
        self.runtime_info_label.setText(display_text)

        # Update mode label and Combo style
        if is_manual:
            self.mode_label.setText("Mode: Manual (Override)")
            self.mode_label.setStyleSheet("color: orange; font-weight: bold;")
            # Visual feedback on combo - Specify color to prevent white-on-white
            self.runtime_info_label.setStyleSheet("color: #d84315;") # Dark orange text
            self.runtime_combo.setStyleSheet("QComboBox { background-color: #fff3e0; color: black; }")
        else:
            self.mode_label.setText("Mode: Auto")
            self.mode_label.setStyleSheet("color: green;")
            self.runtime_info_label.setStyleSheet("color: #2e7d32;") # Green text
            self.runtime_combo.setStyleSheet("")  # Reset style
        
        # Log to console for transparency
        selection_type = "Manual" if is_manual else "Auto"
        self.console_log.append(f"[Runtime {selection_type}] Selected: {rule['name']} (Image: {rule['image']})")

    def _apply_auto_selected_runtime(self, selected_rule):
        """Apply auto-selected runtime to UI controls."""
        if not selected_rule:
            self.selection_mode = 'Manual'
            self.mode_label.setText("Select Runtime (Analysis Failed)")
            self.mode_label.setStyleSheet("color: red; font-weight: bold;")
            return
        self.runtime_combo.blockSignals(True)
        index = self.runtime_combo.findText(selected_rule['name'])
        if index >= 0:
            self.runtime_combo.setCurrentIndex(index)
        else:
            self.console_log.append(f"[Warning] Auto-selected rule '{selected_rule['name']}' not found in list.")
        self.runtime_combo.blockSignals(False)
        self.selection_mode = 'Auto'
        self._update_runtime_display(selected_rule, is_manual=False)


    @Slot()
    def _select_script(self):
        """Open file dialog to select script."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Legacy Python Script", str(Path.home()), "Python Files (*.py)"
        )
        if file_path:
            self.script_path_edit.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.code_editor.setPlainText(content)
                self._run_analysis()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    @Slot()
    def _select_data_dir(self):
        """Open directory dialog to select data dir."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Input Data Directory", str(Path.home())
        )
        if dir_path:
            self.data_dir_edit.setText(dir_path)

    @Slot()
    def _select_output_dir(self):
        """Open directory dialog to select output dir."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(Path.home())
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    @Slot()
    def _run_analysis(self):
        """Analyze code from editor."""
        # 1. Lock UI & Set Status
        self.status_label.setText("Analyzing...")
        self.status_label.repaint()
        self.run_btn.setEnabled(False)
        self.create_env_btn.setEnabled(False)
        self.runtime_combo.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            code_text = self.code_editor.toPlainText()
            if not code_text:
                return

            try:
                view_data = self.code_analysis_use_case.execute(code_text)
                self.version_label.setText(f"Detected Version: {view_data.version}")
                libs_text = ", ".join(view_data.libraries) if view_data.libraries else "None"
                self.libraries_label.setText(f"Detected Libraries: {libs_text}")
                self.sloc_label.setText(f"SLOC: {view_data.sloc}")
                self.ratio_label.setText(f"Comment Ratio: {view_data.comment_ratio:.1f}%")
                self.console_log.append(
                    f"\n[Analysis Completed] Version: {view_data.version}, Libs: {len(view_data.libraries)}, SLOC: {view_data.sloc}"
                )
                self._apply_auto_selected_runtime(view_data.selected_rule)
                
            except Exception as e:
                self.console_log.append(f"\n[Analysis Error] {e}")
                self.selection_mode = 'Manual'
                self.mode_label.setText("Select Runtime (Analysis Failed)")
                self.mode_label.setStyleSheet("color: red; font-weight: bold;")

        finally:
            # Always reset UI state
            self._reset_buttons()


    @Slot()
    def _show_create_env_dialog(self):
        """Show the Environment Creation Dialog."""
        current_content = self.code_editor.toPlainText()
        if not current_content:
            QMessageBox.warning(self, "No Code", "Please select or paste code to analyze first.")
            return

        draft = self.environment_draft_use_case.prepare(current_content)
        rec_id = draft.recommended_rule['id']
        rec_reason = draft.recommendation_reason
        
        # 4. Show Dialog
        # 4. Show Dialog
        dialog = EnvironmentCreationDialog(
            parent=self,
            manager=self.container_manager,
            base_images=draft.base_images,
            initial_config=draft.initial_config,
            recommended_base_id=rec_id,
            recommendation_reason=rec_reason
        )
        
        if dialog.exec():
            # 5. Handle Success
            # The dialog now handles the build process internally.
            
            # Reload definitions to see the new image
            self.container_manager.reload_definitions()
            self._refresh_env_list() # [FIX] Use correct method name
            
            # Select the new environment
            new_config = dialog.result_config
            if new_config:
                tag = new_config.get('tag')
                if tag:
                    # Find and select the new item
                    # Try to match the name (which comes from tag usually)
                    # Our _refresh_env_list adds items by rule['name']
                    # For generated envs, rule['name'] is usually the tag.
                    # Find and select the new item robustly
                    found_idx = -1
                    for i in range(self.runtime_combo.count()):
                        rule = self.runtime_combo.itemData(i, Qt.UserRole)
                        if rule and rule.get('image') == tag:
                            found_idx = i
                            break
                    
                    if found_idx >= 0:
                        self.runtime_combo.setCurrentIndex(found_idx)
                        self._on_runtime_combo_activated(found_idx)
            
            QMessageBox.information(self, "Ready", f"Environment '{tag}' is ready to use.")
            


    def _run_jit_build(self, base_rule, code_content):
        """
        Triggered when a required image is missing.
        Loads existing definition if available, or synthesizes new config.
        """
        rec_id = base_rule['id']
        rec_reason = "Required for execution (Missing Image)"
        
        # Try to load existing definition from disk via Manager
        existing_config = self.container_manager.get_definition(rec_id)
        
        if existing_config:
            print(f"[JIT] Loaded existing definition for '{rec_id}'")
            rec_reason = "Using existing definition (Image not built yet)"
            # [FIX] Explicitly inject ID to ensure dialog locks it
            existing_config['id'] = rec_id
        # Else: existing_config is None, will fall through to synthesis below
        
        # If no existing definition, synthesize new one
        if existing_config is None:
            analysis = self.analyzer.summary(code_content)
            existing_config = self.container_manager.synthesize_definition_config(analysis, rec_id)
            rec_reason = "Synthesized from code analysis (Missing Image)"
            print(f"[JIT] Synthesized config for '{rec_id}' (Fallback)")

        # [CRITICAL FIX] Always inject the requested ID into config
        # This ensures the Dialog treats it as an "Existing Definition" (Locked Name)
        # preventing it from reverting to 'custom-auto-gen' or timestamp.
        if existing_config:
            existing_config['id'] = rec_id
            existing_config['tag'] = rec_id
        
        # === DEBUG LOGGING ===
        print(f"--- [DEBUG] Pre-Dialog Check ---")
        print(f"1. Selected ID from base_rule: '{rec_id}'")
        print(f"2. Config prepared for dialog: {existing_config is not None}")
        if existing_config:
            print(f"3. Config has 'id' key: {'id' in existing_config}")
            print(f"4. Config['id'] value: '{existing_config.get('id', 'MISSING')}'")
            print(f"5. Config['tag'] value: '{existing_config.get('tag', 'MISSING')}'")
        else:
            print("3. Config is None!")
        # === END DEBUG ===
        
        dialog = EnvironmentCreationDialog(
            parent=self,
            manager=self.container_manager,
            base_images=self.container_manager.get_available_runtimes(),
            initial_config=existing_config,
            recommended_base_id=rec_id,
            recommendation_reason=rec_reason
        )
        
        # JIT Dialog handling
        if dialog.exec():
            # Success - Image built
            self.container_manager.reload_definitions()
            self._refresh_env_list()
            
            new_config = dialog.result_config
            if new_config:
                tag = new_config.get('tag')
                self.console_log.append(f"[JIT] Environment '{tag}' created successfully.")
                
                # Update selection robustly
                found_idx = -1
                for i in range(self.runtime_combo.count()):
                    rule = self.runtime_combo.itemData(i, Qt.UserRole)
                    if rule and rule.get('image') == tag:
                        found_idx = i
                        break
                
                if found_idx >= 0:
                    self.runtime_combo.setCurrentIndex(found_idx)
                    self._on_runtime_combo_activated(found_idx)
            
            # Important: JIT flow usually implies we want to run immediately, 
            # but since we just had a blocking dialog, user might want to check things.
            # We reset buttons to allow them to click Run again.
            self._reset_buttons()
            
        else:
            # Cancelled
            self._reset_buttons()


        
    def _reset_buttons(self):
        """Reset UI buttons to active state after operation."""
        self.analyze_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run in Container") # [FIX] Restore text
        self.create_env_btn.setEnabled(True)
        self.runtime_combo.setEnabled(True)  # [FIX] Re-enable combo
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Ready")   # [FIX] Reset status
        self.status_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        print("[UI] Buttons reset to active state.")



    @Slot()
    def _run_container(self):
        """Prepare and run Docker container."""
        script_path = self.script_path_edit.text()
        if not script_path:
            QMessageBox.warning(self, "Warning", "Please select a script first.")
            return
            
        try:
            # New Validation Method
            self.container_manager.validate_environment()
        except Exception as e:
            # JIT: If validating environment logic fails (e.g. docker down), stop.
            # But here we want to catch "Image Missing" in prepare_run_config later?
            # validate_environment only checks Docker Daemon.
            QMessageBox.critical(self, "Docker Error", str(e))
            return

        try:
            current_content = self.code_editor.toPlainText()
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            self.console_log.clear()
            self.console_log.append(f"[Auto-Save] Synchronized editor content to {Path(script_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to auto-save script: {e}")
            return
        
        data_dir = self.data_dir_edit.text() or None
        output_dir = self.output_dir_edit.text() or None
        
        self.run_btn.setText("Running...")
        self.run_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.create_env_btn.setEnabled(False) # Lock New button
        self.stop_btn.setEnabled(True)
        self.runtime_combo.setEnabled(False) # Lock selection

        script_name = Path(script_path).name
        self.status_label.setText(f"Executing: {script_name}...")
        self.status_label.setStyleSheet("font-weight: bold; color: #1976D2;")

        # Switch to Console Tab
        self.tabs.setCurrentIndex(0)
        
        self.console_log.append("Preparing container environment...")
        
        try:
            idx = self.runtime_combo.currentIndex()
            if idx >= 0:
                selected_rule = self.runtime_combo.itemData(idx, Qt.UserRole)
            else:
                selected_rule = None

            preflight = self.runtime_use_case.prepare_run_preflight(
                self.analyzer,
                self.container_manager,
                self.history_manager,
                current_content,
                script_path,
                data_dir=data_dir,
                output_dir=output_dir,
                selected_rule=selected_rule,
                selection_mode=self.selection_mode,
            )
            if preflight.compatibility.requires_confirmation:
                res = QMessageBox.warning(
                    self,
                    "Compatibility Warning",
                    preflight.compatibility.message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if res == QMessageBox.No:
                    self._reset_buttons()
                    self.runtime_combo.setEnabled(True)
                    return

            execution_plan = preflight.execution_plan
            selected_rule = execution_plan.selected_rule
            config = execution_plan.config
            
            # --- JIT Image Check ---
            # Try to verify if image exists using 'docker image inspect'
            image_name = config['image']
            
            # Note: prepare_run_config doesn't return existence, so we check here manually or via helper
            # For robustness, we'll try a lightweight subprocess check
            # Check if image exists
            if preflight.image_missing:
                # Image missing! Prompt JIT Build
                print(f"[Info] Image {image_name} not found. Build is required.")
                ans = QMessageBox.question(
                    self,
                    "Environment Missing",
                    f"The required runtime image '{image_name}' is not built yet.\n\n"
                    "Would you like to synthesize and build it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                
                if ans == QMessageBox.Yes:
                    build_draft = preflight.missing_image_build_draft
                    if not build_draft:
                        self._reset_buttons()
                        return
                    env_id = build_draft.env_id
                    dialog = EnvironmentCreationDialog(
                        parent=self,
                        manager=self.container_manager,
                        base_images=self.container_manager.get_available_runtimes(),
                        initial_config=build_draft.initial_config,
                        recommended_base_id=env_id,
                        recommendation_reason=build_draft.recommendation_reason
                    )
                    
                    # Handle dialog result
                    if dialog.exec():
                        self.container_manager.reload_definitions()
                        self._refresh_env_list()
                        QMessageBox.information(self, "Build Complete", f"Environment '{env_id}' is ready to use.")
                    
                    self._reset_buttons()
                    return  # Exit run flow, build flow completed
                else:
                    self._reset_buttons()
                    return


            # Store output dir for result loading
            self.current_output_dir = config['host_work_dir']
            self.res_timestamp_label.setText(f"Run Timestamp (Latest): {Path(self.current_output_dir).name}")
            self.open_res_btn.setEnabled(False)
            self._clear_results_view()
            
            for line in self.runtime_use_case.build_execution_log_lines(execution_plan):
                self.console_log.append(line)
            self._last_run_context = execution_plan.run_context
            
            self.worker = ContainerWorker(
                docker_args=execution_plan.docker_args,
                script_name=config['script_name']
            )
            
            self.worker.log_updated.connect(self._on_worker_output)
            self.worker.error_occurred.connect(self._on_worker_error)
            self.worker.executionFinished.connect(self._on_worker_finished)
            self.worker.finished.connect(self._ensure_ui_reset)  # Backup cleanup
            
            self.worker.start()
            
        except Exception as e:
            self.console_log.append(f"\n[Setup Error] {e}")
            self._reset_buttons()

    @Slot()
    def _stop_container(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.console_log.append("\n[Stopping...] Request sent to container.")
            self.stop_btn.setEnabled(False)

    @Slot(str)
    def _on_worker_output(self, text):
        self.console_log.append(text)
        sb = self.console_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def _on_worker_error(self, text):
        self.console_log.append(f"<font color='red'>{text}</font>")
        sb = self.console_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(int)
    def _on_worker_finished(self, exit_code):
        status_msg = "Success" if exit_code == 0 else f"Failed (Code {exit_code})"
        color = "lime" if exit_code == 0 else "red"
        self.console_log.append(f"\n<font color='{color}'>--- Execution Finished: {status_msg} ---</font>")
        self._reset_buttons()
        # Scroll to bottom
        sb = self.console_log.verticalScrollBar()
        sb.setValue(sb.maximum())
        
        # Save History
        try:
            if self.current_output_dir:
                idx = self.runtime_combo.currentIndex()
                rule = self.runtime_combo.itemData(idx, Qt.UserRole) if idx >= 0 else None
                reason = self.runtime_use_case.build_history_selection_reason(
                    self.selection_mode, rule
                )
                self.save_history_use_case.save(
                    script_path=self.script_path_edit.text(),
                    runtime_name=self.runtime_combo.currentText(),
                    output_dir=self.current_output_dir,
                    exit_code=exit_code,
                    selection_mode=self.selection_mode,
                    selection_reason=reason,
                    image_tag="docker",
                    audit_metadata=self._build_audit_metadata(exit_code),
                )
                self._refresh_history_list()
                self.console_log.append(f"[History] Record saved ({self.selection_mode}).")
                
        except Exception as e:
            self.console_log.append(f"[History Error] Failed to save record: {e}")
        
        # Unlock Combo
        self.runtime_combo.setEnabled(True)
        
        if exit_code == 0 and self.current_output_dir:
            self.open_res_btn.setEnabled(True)
            self._render_results(self.current_output_dir)
            
    def _clear_results_view(self):
        """Clear the content of the results preview tab."""
        # Remove all widgets from layout
        while self.res_content_layout.count():
            item = self.res_content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _render_results(self, output_dir_str):
        """Render results preview from use-case data."""
        result_data = self.load_result_artifacts_use_case.execute(output_dir_str)
        if not result_data.get("exists"):
            return

        found_files = False
        image_paths = result_data.get("images", [])
        if image_paths:
            found_files = True
            self.res_content_layout.addWidget(QLabel(f"<b>Images ({len(image_paths)}):</b>"))
            for image_path in image_paths:
                img_path = Path(image_path)
                lbl = QLabel()
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    scaled_pix = pixmap.scaled(550, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    lbl.setPixmap(scaled_pix)
                    lbl.setToolTip(img_path.name)
                    lbl.setAlignment(Qt.AlignCenter)
                    img_container = QGroupBox(img_path.name)
                    img_layout = QVBoxLayout()
                    img_layout.addWidget(lbl)
                    img_container.setLayout(img_layout)
                    self.res_content_layout.addWidget(img_container)

        csv_previews = result_data.get("csv_previews", [])
        if csv_previews:
            found_files = True
            self.res_content_layout.addWidget(QLabel(f"<b>CSV Files ({len(csv_previews)}):</b>"))
            for preview in csv_previews:
                self.res_content_layout.addWidget(QLabel(f"📄 {preview['name']}"))
                if not preview.get("previewable", True):
                    self.res_content_layout.addWidget(QLabel("(Cannot preview CSV)"))
                    continue
                headers = preview.get("headers", [])
                rows = preview.get("rows", [])
                if not headers:
                    continue
                table = QTableWidget()
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                table.setRowCount(len(rows))
                for i, cols in enumerate(rows):
                    for j, col in enumerate(cols):
                        if j < len(headers):
                            table.setItem(i, j, QTableWidgetItem(col))
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table.setFixedHeight(150)
                self.res_content_layout.addWidget(table)

        if found_files:
            self.tabs.setCurrentIndex(1)
            self.console_log.append("[Info] Results detected and displayed in 'Results Preview' tab.")
        else:
            self.res_content_layout.addWidget(QLabel("(No obvious artifacts found in output directory)"))

    @Slot()
    def _open_result_folder(self):
        """Open the current result folder in Explorer."""
        if self.current_output_dir:
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_output_dir))
            except Exception as e:
                self.console_log.append(f"[Error] Failed to open folder: {e}")

    def _build_audit_metadata(self, exit_code):
        """Collect and append structured audit metadata."""
        try:
            metadata, lines = self.prepare_audit_metadata_use_case.execute_with_log_lines(
                self._last_run_context, self.current_output_dir, exit_code
            )
            for line in lines:
                self.console_log.append(line)
            return metadata
        except Exception as e:
            self.console_log.append(f"[Audit] metadata_collection_error: {e}")
            return {}

    def update_ui_state(self, state="idle"):
        """Centralized UI state management.
        
        Args:
            state: One of "idle", "running", "building", "analyzing"
        """
        if state == "idle":
            self.run_btn.setText("Run in Container")
            self.run_btn.setEnabled(True)
            self.analyze_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.create_env_btn.setEnabled(True)
            self.runtime_combo.setEnabled(True)
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: #555;")
        
        elif state == "running":
            self.run_btn.setText("Running...")
            self.run_btn.setEnabled(False)
            self.analyze_btn.setEnabled(False)
            self.create_env_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.runtime_combo.setEnabled(False)
            self.status_label.setText("Executing...")
            self.status_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        
        elif state == "building":
            self.run_btn.setEnabled(False)
            self.analyze_btn.setEnabled(False)
            self.create_env_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.runtime_combo.setEnabled(False)
            self.status_label.setText("Building...")
            self.status_label.setStyleSheet("font-weight: bold; color: #d84315;")
        
        elif state == "analyzing":
            self.run_btn.setEnabled(False)
            self.analyze_btn.setText("Analyzing...")
            self.analyze_btn.setEnabled(False)
            self.create_env_btn.setEnabled(False)
            self.runtime_combo.setEnabled(False)
            self.status_label.setText("Analyzing code...")
            self.status_label.setStyleSheet("font-weight: bold; color: #1976d2;")
    
    @Slot()
    def _ensure_ui_reset(self):
        """Backup cleanup called on Worker.finished signal (always fires).
        
        This ensures UI is reset even if other signal handlers fail or aren't connected properly.
        """
        # Only reset if buttons are still locked to avoid double-reset
        if not self.run_btn.isEnabled():
            self.update_ui_state("idle")

    @Slot()
    def _refresh_history_list(self):
        """Reload history from manager."""
        self.history_list.clear()
        records = self.history_manager.load_history()
        # Sort by timestamp descending
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for rec in records:
            ts = rec.get('timestamp', 'N/A')
            status = rec.get('status', 'unknown')
            script = Path(rec.get('script_path', 'unknown')).name
            rt = rec.get('runtime_name', 'unknown')
            
            # Label: [2026-01-01 12:00] Success: script.py (Runtime)
            label = f"[{ts}] {status}: {script} ({rt})"
            item = QListWidgetItem(label)
            
            # Store full record in Data UserRole
            item.setData(Qt.UserRole, rec)
            
            # Color code
            if status != 'success':
                item.setForeground(QColor("red"))
                
            self.history_list.addItem(item)

    @Slot(QListWidgetItem)
    def _on_history_double_clicked(self, item):
        """Open output folder of selected history item."""
        record = item.data(Qt.UserRole)
        if not record:
            return
            
        # relative -> absolute
        rel_path = record.get('output_dir')
        if not rel_path:
            return
            
        abs_path = self.history_manager.get_absolute_path(rel_path)
        if Path(abs_path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
        else:
            QMessageBox.warning(self, "Missing Path", f"Directory not found:\n{abs_path}")

    def _execute_save_and_build(self, config):
        """Save config and trigger build."""
        try:
            available_runtimes = self.container_manager.get_available_runtimes()
            plan = self.environment_build_preparation_use_case.prepare_execution_plan(
                config,
                available_runtimes,
            )
            name = plan.tag
            self.console_log.append(f"[Synthesizer] Definition saved for tag: {name}")
            
            # 2. Reload Manager
            self.container_manager.reload_definitions()
            self._populate_runtime_combo()
            
            # 3. Select New Env
            # Find the new rule
            self.runtime_combo.blockSignals(True)
            index = self.runtime_combo.findText(f"{name} ({name})") # Name format in manager logic: stem (tag)
            # Actually name logic in manager: f"{json_file.stem} ({data.get('tag')})"
            # Our file stem is safe_name.
            # Best effort find:
            if index == -1:
                 # Try finding by data tag
                 for i in range(self.runtime_combo.count()):
                     r = self.runtime_combo.itemData(i, Qt.UserRole)
                     if r['image'] == plan.selected_runtime_image:
                         index = i
                         break
            
            if index >= 0:
                self.runtime_combo.setCurrentIndex(index)
                self.selection_mode = 'Manual'
                # Update display
                self._update_runtime_display(self.runtime_combo.itemData(index, Qt.UserRole), is_manual=True)
            self.runtime_combo.blockSignals(False)
            
            # 4. Trigger Build
            build_args = plan.build_args
            
            self.console_log.append(f"[Build] Starting build for {name}...")
            self.tabs.setCurrentIndex(0) # Show Console
            
            self._start_worker(build_args, f"Build: {name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Build Error", f"Failed to initiate build: {e}")
            self.console_log.append(f"[Build Error] {e}")

    def _run_jit_build(self, rule, code_content):
        """Handle JIT build from Run flow."""
        # 1. Open Dialog pre-filled with this rule?
        # Or if "Synthesize" was clicked, maybe we should offer to Synthesize FROM the missing rule 
        # OR just offer to create a NEW one. 
        # The prompt said "Synthesize and build".
        # Let's open the Dialog, pre-set with what we know.
        self._show_create_env_dialog()

    def _start_worker(self, args, script_name):
        """Common worker starter."""
        self.run_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.create_env_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.runtime_combo.setEnabled(False)
        
        self.worker = ContainerWorker(
            docker_args=args,
            script_name=script_name
        )
        self.worker.log_updated.connect(self._on_worker_output)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.executionFinished.connect(self._on_worker_finished)
        self.worker.start()

    def closeEvent(self, event):
        """Handle window close event to ensure cleanup."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(event)
