# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Container worker for executing Docker containers in background threads.

This module provides ContainerWorker which:
- Executes Docker containers in a QThread
- Streams output via signals
- Handles errors and cleanup properly
- Based on LCR's TrainingWorker pattern
"""

import subprocess
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal


class ContainerWorker(QThread):
    """
    Worker thread for executing Docker containers.
    
    Refactored from LCR's TrainingWorker to execute legacy code
    in Docker containers with real-time output streaming.
    
    Signals:
        output_ready(str): Emitted when new output line is available
        error_occurred(str): Emitted when an error occurs
        finished_with_code(int): Emitted when execution completes with exit code
    """
    
    # Signals
    log_updated = Signal(str)
    error_occurred = Signal(str)
    finished_with_code = Signal(int)
    
    def __init__(
        self, 
        docker_args: list,
        script_name: str = "script",
        parent=None
    ):
        """
        Initialize the ContainerWorker.
        
        Args:
            docker_args: Complete docker run command arguments
            script_name: Name of script being executed (for logging)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.docker_args = docker_args
        self.script_name = script_name
        self.process: Optional[subprocess.Popen] = None
        self._stop_requested = False
    
    def run(self):
        """Execute the Docker container (runs in background thread)."""
        try:
            self.log_updated.emit("=" * 70)
            self.log_updated.emit(f"Starting container execution: {self.script_name}")
            self.log_updated.emit("=" * 70)
            self.log_updated.emit(f"Command: {' '.join(self.docker_args)}")
            self.log_updated.emit("")
            
            # Start Docker process
            self.process = subprocess.Popen(
                self.docker_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output line by line
            for line in iter(self.process.stdout.readline, ''):
                if self._stop_requested:
                    self.log_updated.emit("\n[Execution stopped by user]")
                    break
                
                if line:
                    self.log_updated.emit(line.rstrip())
            
            # Wait for process to complete
            if not self._stop_requested:
                returncode = self.process.wait()
                
                self.log_updated.emit("")
                self.log_updated.emit("=" * 70)
                if returncode == 0:
                    self.log_updated.emit(f"Container execution completed successfully (exit code: {returncode})")
                else:
                    self.log_updated.emit(f"Container execution failed (exit code: {returncode})")
                self.log_updated.emit("=" * 70)
                
                self.finished_with_code.emit(returncode)
            else:
                self.finished_with_code.emit(-1)
        
        except FileNotFoundError:
            error_msg = (
                "Docker command not found. Please ensure Docker is installed and "
                "available in your system PATH."
            )
            self.error_occurred.emit(error_msg)
            self.finished_with_code.emit(-1)
        
        except Exception as e:
            import traceback
            error_msg = f"Error executing container:\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)
            self.finished_with_code.emit(-1)
        
        finally:
            self._cleanup()
            
    def stop(self):
        """Request the worker to stop execution and kill the container process."""
        self._stop_requested = True
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources and kill subprocess."""
        if self.process:
            try:
                if self.process.poll() is None:
                    # Terminate first
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Kill if stubborn
                        self.process.kill()
                        self.log_updated.emit("Force killed container process.")
            except Exception:
                pass
            self.process = None

