"""
Legacy Code Reviver - Proof of Concept

This script demonstrates the complete LCR workflow:
1. Analyze legacy Python code
2. Select appropriate Docker image
3. Execute code in container
4. Stream output to console

Usage:
    python run_lcr_poc.py
"""

import sys
from pathlib import Path

# Check imports for PySide6 verification (as requested)
try:
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication
except ImportError:
    print("[FATAL] PySide6 not installed or import failed.")
    sys.exit(1)

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager
from lcr.core.container.worker import ContainerWorker


class LCRDemo:
    """Demonstration of Legacy Code Reviver workflow."""
    
    def __init__(self):
        # Use QCoreApplication for non-GUI event loop
        self.app = QCoreApplication(sys.argv)
        self.worker = None
        self.exit_code = 0
    
    def run(self):
        """Execute the complete LCR workflow."""
        print("\n" + "=" * 70)
        print("  Legacy Code Reviver - Proof of Concept")
        print("=" * 70)
        print("  [CHECK] PySide6 imports successful")
        
        # Step 1: Analyze code
        script_path = project_root / 'data' / 'samples' / 'python2_basic.py'
        print(f"\n[STEP 1] Analyzing: {script_path.name}")
        print("-" * 70)
        
        if not script_path.exists():
            print(f"[ERROR] Script not found: {script_path}")
            return 1
        
        analyzer = CodeAnalyzer()
        with open(script_path, 'r', encoding='utf-8') as f:
            code_text = f.read()
        
        analysis = analyzer.summary(code_text)
        
        print(f"  Python Version: {analysis['version']}")
        print(f"  Libraries: {', '.join(analysis['libraries']) if analysis['libraries'] else 'None'}")
        
        # Step 2: Select Docker image
        print(f"\n[STEP 2] Selecting Docker Image")
        print("-" * 70)
        
        manager = ContainerManager()
        image = manager.select_image(analysis)
        print(f"  Selected Image: {image}")
        
        # Step 3: Prepare configuration
        print(f"\n[STEP 3] Preparing Container Configuration")
        print("-" * 70)
        
        config = manager.prepare_run_config(analysis, str(script_path))
        print(f"  Host Directory: {config['host_work_dir']}")
        print(f"  Container Work Dir: {config['working_dir']}")
        print(f"  Script: {config['script_name']}")
        
        # Step 4: Execute in container
        print(f"\n[STEP 4] Executing in Docker Container (via ContainerWorker)")
        print("-" * 70)
        
        docker_args = manager.get_docker_run_args(config)
        
        # Create worker (using PySide6 QThread)
        self.worker = ContainerWorker(
            docker_args=docker_args,
            script_name=config['script_name']
        )
        
        # Connect signals
        self.worker.output_ready.connect(self.on_output)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.finished_with_code.connect(self.on_finished)
        
        # Start execution
        self.worker.start()
        
        # Run event loop
        return self.app.exec()
    
    def on_output(self, line: str):
        """Handle output from container."""
        print(line)
    
    def on_error(self, error: str):
        """Handle errors."""
        print(f"\n[ERROR] {error}", file=sys.stderr)
        self.exit_code = 1
    
    def on_finished(self, exit_code: int):
        """Handle completion."""
        self.exit_code = exit_code
        
        print("\n" + "=" * 70)
        print("  LCR Workflow Complete")
        print("=" * 70)
        print(f"  Exit Code: {exit_code}")
        
        if exit_code == 0:
            print("  Status: SUCCESS")
        else:
            print("  Status: FAILED")
        
        print("=" * 70 + "\n")
        
        # Quit application
        self.app.quit()


def main():
    """Main entry point."""
    try:
        demo = LCRDemo()
        exit_code = demo.run()
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
