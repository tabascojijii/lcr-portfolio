from typing import TypedDict, Optional

class ExecutionHistory(TypedDict):
    """
    Represents a single execution record.
    Paths should be stored as relative paths to project root for portability.
    """
    id: str           # UUID
    timestamp: str    # ISO format or YYYYMMDD_HHMMSS
    script_path: str  # Relative path to script
    runtime_name: str # e.g. "Python 2.7 + OpenCV"
    image_tag: str    # e.g. lcr-py27-cv-apt
    output_dir: str   # Relative path to output directory
    status: str       # success, failed, etc.
