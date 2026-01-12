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
import io
import subprocess
import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QTextEdit,
    QGroupBox, QFileDialog, QMessageBox, QApplication, QTabWidget,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem, QComboBox
)
from PySide6.QtGui import QFont, QColor, QPixmap, QDesktopServices
from PySide6.QtCore import Qt, Slot, QUrl

from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager
from lcr.core.container.worker import ContainerWorker
from lcr.core.container.generator import generate_dockerfile, save_definition
from lcr.core.history.manager import HistoryManager
from lcr.core.history.types import ExecutionHistory
from lcr.ui.create_env_dialog import EnvironmentCreationDialog
from utils.count_loc import count_lines_python


class MainWindow(QMainWindow):
    """Main window of the application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Legacy Code Reviver")
        self.resize(1200, 800)

        # backend components
        self.analyzer = CodeAnalyzer()
        self.container_manager = ContainerManager()
        self.history_manager = HistoryManager()
        self.worker = None
        self.worker = None
        self.current_output_dir = None
        self.selection_mode = 'Auto'


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
        self._populate_runtime_combo()
        
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

    def _populate_runtime_combo(self):
        """Populate the runtime combobox from ContainerManager rules."""
        self.runtime_combo.clear()
        rules = self.container_manager.get_available_runtimes()
        for i, rule in enumerate(rules):
            self.runtime_combo.addItem(rule['name'])
            # Store full rule in UserRole
            self.runtime_combo.setItemData(i, rule, Qt.UserRole)
            # Tooltip: Base Image
            desc = rule.get('description', f"Image: {rule['image']}")
            self.runtime_combo.setItemData(i, desc, Qt.ToolTipRole)

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
                result = self.analyzer.summary(code_text)
                version = result.get('version', 'Unknown')
                libraries = result.get('libraries', [])
                
                self.version_label.setText(f"Detected Version: {version}")
                self.libraries_label.setText(f"Detected Libraries: {', '.join(libraries) if libraries else 'None'}")
                
                stream = io.BytesIO(code_text.encode('utf-8'))
                total, code, comments = count_lines_python(stream)
                
                ratio = 0.0
                if (code + comments) > 0:
                    ratio = (comments / (code + comments)) * 100
                    
                self.sloc_label.setText(f"SLOC: {code}")
                self.ratio_label.setText(f"Comment Ratio: {ratio:.1f}%")
                
                self.console_log.append(f"\n[Analysis Completed] Version: {version}, Libs: {len(libraries)}, SLOC: {code}")
                
                # --- Auto Select Runtime ---
                try:
                    # 1. Analyze for features (needed for resolution)
                    feature = self.analyzer.analyze(code_text)
                    version_hint = feature.version_hint
                    search_terms = feature.imports + feature.keywords
                    if feature.validation_year:
                         search_terms.append(f"year:{feature.validation_year}")
                    
                    # 2. Resolve
                    selected_rule = self.container_manager.resolve_runtime(search_terms, version_hint)
                    
                    # 3. Update Combo (Silent)
                    self.runtime_combo.blockSignals(True)
                    index = self.runtime_combo.findText(selected_rule['name'])
                    if index >= 0:
                        self.runtime_combo.setCurrentIndex(index)
                    else:
                        self.console_log.append(f"[Warning] Auto-selected rule '{selected_rule['name']}' not found in list.")
                    self.runtime_combo.blockSignals(False)
                    
                    # 4. Reset Mode and Update Display
                    self.selection_mode = 'Auto'
                    self._update_runtime_display(selected_rule, is_manual=False)
                    
                except Exception as e:
                    self.console_log.append(f"[Analysis Error - AutoSelect] {e}")
                    # Fallback to Manual Mode on error
                    self.selection_mode = 'Manual'
                    self.mode_label.setText("Select Runtime (Analysis Failed)")
                    self.mode_label.setStyleSheet("color: red; font-weight: bold;")
                
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

        # 1. Analyze
        # We assume the user wants to base the env on the CURRENT code
        analysis = self.analyzer.summary(current_content)
        
        # 2. Get Recommendation
        feature = self.analyzer.analyze(current_content)
        search_terms = feature.imports + feature.keywords
        if feature.validation_year:
             search_terms.append(f"year:{feature.validation_year}")
        
        recommended_rule = self.container_manager.resolve_runtime(search_terms, feature.version_hint)
        rec_id = recommended_rule['id']
        rec_reason = recommended_rule.get('reason', 'Best match')

        # 3. Synthesize Initial Config
        # This uses the new logic in manager to calculate diffs
        initial_config = self.container_manager.synthesize_definition_config(analysis, rec_id)
        
        # 4. Show Dialog
        dialog = EnvironmentCreationDialog(
            self, 
            self.container_manager.get_available_runtimes(),
            initial_config,
            rec_id,
            rec_reason
        )
        
        if dialog.exec():
            # 5. Handle Save & Build
            new_config = dialog.result_config
            if new_config:
                try:
                    # Save JSON
                    json_path = save_definition(new_config, new_config['tag'])
                    self.console_log.append(f"[Generator] Definition saved to {json_path.name}")
                    
                    # Generate Dockerfile
                    tag, dockerfile_path = generate_dockerfile(str(json_path))
                    
                    # Run Build
                    self._run_docker_build(dockerfile_path, tag)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Generation Error", str(e))
                    self.console_log.append(f"[Generation Error] {e}")

    def _run_jit_build(self, base_rule, code_content):
        """
        Triggered when a required image is missing.
        Pre-fills the creation dialog with the missing image's rule info effectively.
        """
        # We can re-use the show dialog logic but maybe tweak the initial reason
        # Actually simplified: just call _show_create_env_dialog, 
        # as it analyzes the code and will likely recommend the same thing (or similar).
        # But to be precise, we pass the rule we TRIED to use as the recommendation.
        
        analysis = self.analyzer.summary(code_content)
        rec_id = base_rule['id']
        rec_reason = "Required for execution (Missing Image)"
        
        initial_config = self.container_manager.synthesize_definition_config(analysis, rec_id)
        
        dialog = EnvironmentCreationDialog(
            self, 
            self.container_manager.get_available_runtimes(),
            initial_config,
            rec_id,
            rec_reason
        )
        
        if dialog.exec():
            new_config = dialog.result_config
            if new_config:
                try:
                    json_path = save_definition(new_config, new_config['tag'])
                    self.console_log.append(f"[JIT] Definition saved to {json_path.name}")
                    tag, dockerfile_path = generate_dockerfile(str(json_path))
                    self._run_docker_build(dockerfile_path, tag)
                except Exception as e:
                    QMessageBox.critical(self, "Build Error", str(e))
                    self._reset_buttons()
        else:
            # If user cancels JIT dialog, we must unlock the UI (locked in _run_container)
            self._reset_buttons()

    def _run_docker_build(self, dockerfile_path: str, tag: str):
        """Execute docker build command via Worker."""
        build_args = self.container_manager.get_build_command(dockerfile_path, tag)
        
        self.console_log.append(f"\n[Builder] Starting build for '{tag}'...")
        self.console_log.append(f"Command: {' '.join(build_args)}")
        
        # Switch to console
        self.tabs.setCurrentIndex(0)
        self.run_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False) # Lock analyze
        self.create_env_btn.setEnabled(False) # Lock new
        self.stop_btn.setEnabled(True) # Allow cancelling build
        
        self.status_label.setText(f"Building Image: {tag}...")
        self.status_label.setStyleSheet("font-weight: bold; color: #d84315;")
        
        # Reuse ContainerWorker since it just runs a subprocess
        self.worker = ContainerWorker(
            docker_args=build_args,
            script_name=f"BUILD:{tag}"
        )
        
        # We need a special finished handler to reload definitions after build
        self.worker.log_updated.connect(self._on_worker_output)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.finished.connect(self._ensure_ui_reset)  # Backup cleanup
        
        # Define a closure or separate slot for build completion
        # Using lambda strictly for the slot connection might be risky if we need robust teardown
        # So we'll use a specific slot but we need to know it was a build.
        # Hack: Check script_name in _on_worker_finished? 
        # Better: create a dedicated _on_build_finished wrapper
        
        self.worker.finished_with_code.connect(lambda c: self._on_build_finished(c, tag))
        
        self.worker.start()

    def _on_build_finished(self, exit_code, tag):
        """Handle build completion."""
        status = "Success" if exit_code == 0 else "Failed"
        color = "lime" if exit_code == 0 else "red"
        self.console_log.append(f"<font color='{color}'>[Builder] Build {status} for '{tag}'</font>")
        
        self._reset_buttons()  # This now includes create_env_btn and runtime_combo
        
        if exit_code == 0:
            # Reload Manager
            self.container_manager.reload_definitions()
            self._populate_runtime_combo()
            
            # Select the new tag
            self.runtime_combo.blockSignals(True)
            idx = self.runtime_combo.findText(f"{tag} ({tag})") # Name format might vary
            # Our name format in manager is "{stem} ({tag})"
            # We don't know the exact stem (filename) easily here without logic.
            # Loose search by tag in item data
            found = False
            for i in range(self.runtime_combo.count()):
                rule = self.runtime_combo.itemData(i, Qt.UserRole)
                if rule and rule.get('image') == tag:
                    self.runtime_combo.setCurrentIndex(i)
                    self._update_runtime_display(rule, is_manual=True) # treat as manual selection of the new env
                    found = True
                    break
            
            if not found:
                self.console_log.append(f"[Builder] Warning: Could not auto-select new image '{tag}'. Please select manually.")
                
            self.runtime_combo.blockSignals(False)
            QMessageBox.information(self, "Build Complete", f"Environment '{tag}' created and selected.")

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
            # 3. Analyze for Image Selection (refresh to be sure)
            feature = self.analyzer.analyze(current_content)
            
            # Select Image based on analysis
            # Using new resolve_runtime methodology
            version_hint = feature.version_hint
            search_terms = feature.imports + feature.keywords
            if feature.validation_year:
                 search_terms.append(f"year:{feature.validation_year}")
            
            # 4. Config
            # Note: prepare_run_config internally calls select_image/resolve_runtime 
            # We will use it directly to get standard config but we can double check the reasoning here for display
            
            # Get reasoning explicitly for UI display
            # If Manual, use the ComboBox selected item
            idx = self.runtime_combo.currentIndex()
            if idx >= 0:
                 selected_rule = self.runtime_combo.itemData(idx, Qt.UserRole)
            else:
                 selected_rule = self.container_manager.resolve_runtime(search_terms, version_hint)

            # Manual Compatibility Check UI
            if self.selection_mode == 'Manual':
                 rule_ver = selected_rule.get('version', 'unknown')
                 feature = self.analyzer.analyze(current_content)
                 code_ver = feature.version_hint
                 
                 if not self.container_manager._check_version_compat(code_ver, rule_ver):
                     res = QMessageBox.warning(
                         self, 
                         "Compatibility Warning",
                         f"You selected {rule_ver} but the code appears to be {code_ver}.\n\nUsage mistakes may cause errors. Continue?",
                         QMessageBox.Yes | QMessageBox.No,
                         QMessageBox.No
                     )
                     if res == QMessageBox.No:
                         self._reset_buttons()
                         self.runtime_combo.setEnabled(True)
                         return
            
            # Construct explanation
            
            # Construct explanation
            reasons = []
            if feature.validation_year:
                reasons.append(f"Validation Year ({feature.validation_year}) detected")
            
            matches = [t for t in selected_rule.get('triggers', []) if t in search_terms]
            if matches:
                reasons.append(f"Triggers {matches} detected")
                
            match_libs = set(selected_rule.get('libs', [])).intersection(set(search_terms))
            if match_libs:
                reasons.append(f"Libraries {list(match_libs)} matched")
                
            reason_text = " / ".join(reasons) if reasons else "Default selection"

            # Use Manager to prepare config
            # Check for image existence before running
            config = self.container_manager.prepare_run_config(
                self.analyzer.summary(current_content), 
                script_path, 
                data_dir=data_dir,
                output_dir=output_dir,
                override_image_rule=selected_rule 
            )
            
            # --- JIT Image Check ---
            # Try to verify if image exists using 'docker image inspect'
            image_name = config['image']
            
            # Note: prepare_run_config doesn't return existence, so we check here manually or via helper
            # For robustness, we'll try a lightweight subprocess check
            try:
                subprocess.run(
                    ["docker", "image", "inspect", image_name], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL, 
                    check=True
                )
            except subprocess.CalledProcessError:
                # Image missing! Prompt JIT Build
                ans = QMessageBox.question(
                    self,
                    "Environment Missing",
                    f"The required runtime image '{image_name}' is not built yet.\n\n"
                    "Would you like to synthesize and build it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if ans == QMessageBox.Yes:
                    self._run_jit_build(selected_rule, current_content) 
                    return # Exit run flow, switch to build flow
                else:
                    self._reset_buttons()
                    return


            docker_args = self.container_manager.get_docker_run_args(config)

            
            # Store output dir for result loading
            self.current_output_dir = config['host_work_dir']
            self.res_timestamp_label.setText(f"Run Timestamp (Latest): {Path(self.current_output_dir).name}")
            self.open_res_btn.setEnabled(False)
            self._clear_results_view()
            
            self.console_log.append(f"Output Directory (Host): {self.current_output_dir}")
            self.console_log.append(f"\n[Environment Decision Engine]")
            self.console_log.append(f"Selected Runtime: {selected_rule.get('name', config['image'])}")
            self.console_log.append(f"Reason: {reason_text}")
            self.console_log.append(f"Image Tag: {config['image']}")
            
            self.worker = ContainerWorker(
                docker_args=docker_args,
                script_name=config['script_name']
            )
            
            self.worker.log_updated.connect(self._on_worker_output)
            self.worker.error_occurred.connect(self._on_worker_error)
            self.worker.finished_with_code.connect(self._on_worker_finished)
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
                import uuid
                
                # Determine detailed reason
                reason = "Unknown"
                if self.selection_mode == 'Manual':
                    # Get selected tag
                    idx = self.runtime_combo.currentIndex()
                    rule = self.runtime_combo.itemData(idx, Qt.UserRole)
                    tag = rule['image'] if rule else "unknown"
                    reason = f"Manual: {tag}"
                else:
                    # Auto reason (would be nice to capture from resolve_runtime log, but for now simple)
                    reason = "Auto: Detected"
                
                record: ExecutionHistory = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
                    "script_path": self.script_path_edit.text(),
                    "runtime_name": self.runtime_combo.currentText(),
                    "image_tag": "docker", # Placeholder or actual image
                    "output_dir": self.current_output_dir,
                    "status": "success" if exit_code == 0 else "failed",
                    "selection_mode": self.selection_mode,
                    "selection_reason": reason
                }
                self.history_manager.save_record(record)
                self._refresh_history_list()
                self.console_log.append(f"[History] Record saved ({self.selection_mode}).")
                
        except Exception as e:
            self.console_log.append(f"[History Error] Failed to save record: {e}")
        
        # Unlock Combo
        self.runtime_combo.setEnabled(True)
        
        if exit_code == 0 and self.current_output_dir:
            self.open_res_btn.setEnabled(True)
            self._load_results(self.current_output_dir)
            
    def _clear_results_view(self):
        """Clear the content of the results preview tab."""
        # Remove all widgets from layout
        while self.res_content_layout.count():
            item = self.res_content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _load_results(self, output_dir_str):
        """Scan output directory and display results."""
        out_dir = Path(output_dir_str)
        if not out_dir.exists():
            return
            
        found_files = False
        
        # Images
        image_files = sorted(list(out_dir.glob("*.png")) + list(out_dir.glob("*.jpg")) + list(out_dir.glob("*.jpeg")))
        if image_files:
            found_files = True
            self.res_content_layout.addWidget(QLabel(f"<b>Images ({len(image_files)}):</b>"))
            for img_path in image_files:
                lbl = QLabel()
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    # Scale to fit width if too large
                    scaled_pix = pixmap.scaled(550, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    lbl.setPixmap(scaled_pix)
                    lbl.setToolTip(img_path.name)
                    lbl.setAlignment(Qt.AlignCenter)
                    
                    # Container for title + image
                    img_container = QGroupBox(img_path.name)
                    img_layout = QVBoxLayout()
                    img_layout.addWidget(lbl)
                    img_container.setLayout(img_layout)
                    self.res_content_layout.addWidget(img_container)
        
        # CSVs
        csv_files = sorted(list(out_dir.glob("*.csv")))
        if csv_files:
            found_files = True
            self.res_content_layout.addWidget(QLabel(f"<b>CSV Files ({len(csv_files)}):</b>"))
            for csv_path in csv_files:
                self.res_content_layout.addWidget(QLabel(f"📄 {csv_path.name}"))
                # Simple preview of first 5 lines
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        lines = [f.readline().strip() for _ in range(5)]
                        lines = [l for l in lines if l] # filter empty
                        
                    if lines:
                        # Parse header
                        headers = lines[0].split(',') # Basic split
                        table = QTableWidget()
                        table.setColumnCount(len(headers))
                        table.setHorizontalHeaderLabels(headers)
                        table.setRowCount(len(lines) - 1 if len(lines) > 1 else 0)
                        
                        for i, line in enumerate(lines[1:]):
                            cols = line.split(',')
                            for j, col in enumerate(cols):
                                if j < len(headers):
                                    table.setItem(i, j, QTableWidgetItem(col))
                        
                        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                        table.setFixedHeight(150) # Limit height
                        self.res_content_layout.addWidget(table)
                except Exception:
                    self.res_content_layout.addWidget(QLabel("(Cannot preview CSV)"))

        if found_files:
            # Switch tab to notify user
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

    @Slot()
    def _show_create_env_dialog(self):
        """Open dialog to create new environment based on current code."""
        code_text = self.code_editor.toPlainText()
        if not code_text:
            QMessageBox.warning(self, "Info", "Please load a script first to detect dependencies.")
            return

        # 1. Analyze
        # Reuse logic?
        feature = self.analyzer.analyze(code_text)
        summary = self.analyzer.summary(code_text)
        
        # 2. Get available bases
        all_rules = self.container_manager.get_available_runtimes()
        
        # 3. Smart Base Recommendation
        # Use existing logical resolution to pick the best base
        version_hint = feature.version_hint
        search_terms = feature.imports + feature.keywords
        if feature.validation_year:
             search_terms.append(f"year:{feature.validation_year}")
             
        recommended_rule = self.container_manager.resolve_runtime(search_terms, version_hint)
        recommended_id = recommended_rule.get('id')
        
        # Formulate reason
        ver_reason = f"Version {version_hint}"
        term_reason = f"Matches: {', '.join(search_terms[:3])}..." if search_terms else "Generic"
        rec_reason = f"Recommended based on: {ver_reason}. {term_reason}"

        # 4. Synthesize Config
        config_suggestion = self.container_manager.synthesize_definition_config(summary, recommended_id)
        
        dialog = EnvironmentCreationDialog(
            self, 
            base_images=all_rules, 
            initial_config=config_suggestion,
            recommended_base_id=recommended_id,
            recommendation_reason=rec_reason
        )
        
        if dialog.exec():
            final_config = dialog.result_config
            if final_config:
                self._execute_save_and_build(final_config)

    def _execute_save_and_build(self, config):
        """Save config and trigger build."""
        try:
            name = config['tag']
            # 1. Save
            json_path = save_definition(config, name)
            self.console_log.append(f"[Synthesizer] Definition saved: {json_path}")
            
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
                     if r['image'] == name:
                         index = i
                         break
            
            if index >= 0:
                self.runtime_combo.setCurrentIndex(index)
                self.selection_mode = 'Manual'
                # Update display
                self._update_runtime_display(self.runtime_combo.itemData(index, Qt.UserRole), is_manual=True)
            self.runtime_combo.blockSignals(False)
            
            # 4. Generate Dockerfile (for build context)
            tag, dockerfile_path = generate_dockerfile(config)
            
            # 5. Trigger Build
            build_args = self.container_manager.get_build_command(dockerfile_path, tag)
            
            self.console_log.append(f"[Build] Starting build for {tag}...")
            self.tabs.setCurrentIndex(0) # Show Console
            
            self._start_worker(build_args, f"Build: {tag}")
            
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
        self.worker.finished_with_code.connect(self._on_worker_finished)
        self.worker.start()

    def closeEvent(self, event):
        """Handle window close event to ensure cleanup."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(event)
