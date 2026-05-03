# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""Container process runner (framework-agnostic)."""

import subprocess
from typing import Callable, Optional


class ContainerExecutionService:
    """Pure Python service for running Docker process with streamed logs."""

    def __init__(self, docker_args: list, script_name: str = "script"):
        self.docker_args = docker_args
        self.script_name = script_name
        self.process: Optional[subprocess.Popen] = None
        self._stop_requested = False

    def execute(
        self,
        on_log: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> int:
        """Execute Docker command and stream outputs via callbacks."""
        exit_code = -1
        try:
            on_log("=" * 70)
            on_log(f"Starting container execution: {self.script_name}")
            on_log("=" * 70)
            on_log(f"Command: {' '.join(self.docker_args)}")
            on_log("")

            self.process = subprocess.Popen(
                self.docker_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )

            for line in iter(self.process.stdout.readline, ''):
                if self._stop_requested:
                    on_log("\n[Execution stopped by user]")
                    break
                if line:
                    on_log(line.rstrip())

            if not self._stop_requested:
                exit_code = self.process.wait()
                on_log("")
                on_log("=" * 70)
                if exit_code == 0:
                    on_log(f"Container execution completed successfully (exit code: {exit_code})")
                else:
                    on_log(f"Container execution failed (exit code: {exit_code})")
                on_log("=" * 70)
            else:
                exit_code = -1
        except FileNotFoundError:
            on_error("Docker command not found. Please ensure Docker is installed and available in your system PATH.")
            exit_code = -1
        except Exception as e:
            import traceback
            on_error(f"Error executing container:\n{traceback.format_exc()}")
            exit_code = -1
        finally:
            self._cleanup()
        return exit_code

    def stop(self):
        """Request stop and terminate subprocess."""
        self._stop_requested = True
        self._cleanup()

    def _cleanup(self):
        """Clean up running process."""
        if self.process:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
            except Exception:
                pass
            self.process = None

