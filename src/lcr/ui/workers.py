# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
UI Workers for LCR application.
Includes specific workers for Docker builds and other long-running tasks.
"""

import subprocess
import os
import signal
from typing import Optional, List
from PySide6.QtCore import QThread, Signal

class BuildWorker(QThread):
    """
    Worker thread to execute Docker builds with real-time log streaming.
    
    Attributes:
        docker_args (List[str]): The command line arguments for the build.
        tag (str): The tag name of the image being built.
    """
    
    # Signal emitted when a new log line is received (text)
    log_received = Signal(str)
    
    # Signal emitted when build finishes (exit_code, tag)
    build_finished = Signal(int, str)
    
    def __init__(self, docker_args: List[str], tag: str, parent=None):
        super().__init__(parent)
        self.docker_args = docker_args
        self.tag = tag
        self.process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def run(self):
        """Execute the build process."""
        self._is_cancelled = False
        
        # Prepare startup info for Windows to hide the console window
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # useshowwindow is 0 (SW_HIDE) by default when flag is set
        
        try:
            self.log_received.emit(f"STARTING BUILD: {self.tag}")
            self.log_received.emit(f"Command: {' '.join(self.docker_args)}\n")
            
            # [REQ-2] Encoding safety: Use utf-8 with replacement for robustness
            self.process = subprocess.Popen(
                self.docker_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                text=True,
                encoding='utf-8',
                errors='replace',  # Visual safety for mixed encoding output
                bufsize=1  # Line buffered
            )
            
            # Stream output
            for line in iter(self.process.stdout.readline, ''):
                if self._is_cancelled:
                    break
                if line:
                    self.log_received.emit(line.rstrip())
            
            # Wait for completion
            if not self._is_cancelled:
                self.process.wait()
                exit_code = self.process.returncode
            else:
                exit_code = -1  # Cancelled
            
            self.build_finished.emit(exit_code, self.tag)
            
        except FileNotFoundError:
            self.log_received.emit("Error: Docker executable not found.")
            self.build_finished.emit(127, self.tag)
        except Exception as e:
            self.log_received.emit(f"Error starting build process: {str(e)}")
            self.build_finished.emit(1, self.tag)
        finally:
            self._cleanup()

    def stop(self):
        """
        [REQ-3] Stop the build immediately.
        Force kills the process to ensure quick cancellation.
        """
        self._is_cancelled = True
        self.log_received.emit("\n[!] Cancellation requested. Stopping build process...")
        self._cleanup()

    def _cleanup(self):
        """Internal cleanup helper to kill process."""
        if self.process:
            try:
                # [REQ-3] Robust kill
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=1)
            except Exception as e:
                # Last resort catch to prevent worker crash during cleanup
                print(f"Error cleaning up build process: {e}")
            finally:
                self.process = None
