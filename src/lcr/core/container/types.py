from typing import List, Dict, Optional, TypedDict
from dataclasses import dataclass, field

class ImageRule(TypedDict):
    id: str
    name: str
    version: str
    libs: List[str]
    image: str
    prepend_python: bool
    triggers: List[str]

class VolumeConfig(TypedDict):
    bind: str
    mode: str

class RunConfig(TypedDict):
    image: str
    volumes: Dict[str, VolumeConfig]
    working_dir: str
    command: List[str]
    script_name: str
    host_work_dir: str

@dataclass
class CodeFeature:
    """Mirrors the definition in analyzer.py for type hinting."""
    validation_year: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    version_hint: str = "unknown"

class AnalysisResult(TypedDict):
    version: str
    libraries: List[str]
    keywords: List[str]
    validation_year: Optional[str]
    feature_object: CodeFeature
