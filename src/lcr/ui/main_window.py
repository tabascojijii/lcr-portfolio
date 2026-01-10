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
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QFont, QColor, QPixmap, QDesktopServices
from PySide6.QtCore import Qt, Slot, QUrl

from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager
from lcr.core.container.worker import ContainerWorker
from lcr.core.history.manager import HistoryManager
from lcr.core.history.types import ExecutionHistory
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
        self.current_output_dir = None

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

        # Add right pane to splitter
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])

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
            
        except Exception as e:
            self.console_log.append(f"\n[Analysis Error] {e}")

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
        
        self.run_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
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
            selected_rule = self.container_manager.resolve_runtime(search_terms, version_hint)
            
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

            # Use Manager to prepare config (it will re-resolve but consistency is fine)
            # Future refactor: pass 'rule' to prepare_run_config to avoid double resolution
            config = self.container_manager.prepare_run_config(
                self.analyzer.summary(current_content), # Pass legacy summary for compatibility
                script_path, 
                data_dir=data_dir,
                output_dir=output_dir
            )
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
            if self.current_output_dir: # Ensure we have context
                import uuid
                # Reconstruct context (ideally worker should pass this back, but we have UI state)
                # Note: We rely on self.script_path_edit.text() assuming it hasn't changed.
                # A safer way is to store the run context when starting the worker.
                # For now, we use current UI state which is generally fine for single worker.
                
                # Check Console Log for runtime info we printed earlier? 
                # Better: Use what we stored or just generic info if missing.
                # Since we don't persist the 'config' object in self, we'll approximate 
                # or just use what we have.
                # Actually, relying on UI state is risky if user changed it during run.
                # But LCR is modal-ish (buttons disabled).
                
                record: ExecutionHistory = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.datetime.now().replace(microsecond=0).isoformat(),
                    "script_path": self.script_path_edit.text(),
                    "runtime_name": "Docker Container", # Simplified
                    "image_tag": "unknown", # We didn't save this in self
                    "output_dir": self.current_output_dir,
                    "status": "success" if exit_code == 0 else "failed"
                }
                self.history_manager.save_record(record)
                self._refresh_history_list()
                self.console_log.append(f"[History] Record saved.")
                
        except Exception as e:
            self.console_log.append(f"[History Error] Failed to save record: {e}")
        
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

    def _reset_buttons(self):
        self.run_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

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

    def closeEvent(self, event):
        """Handle window close event to ensure cleanup."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(event)
