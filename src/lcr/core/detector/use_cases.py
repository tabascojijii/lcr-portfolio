import io
from dataclasses import dataclass
from typing import Dict, List, Optional

from utils.count_loc import count_lines_python


@dataclass
class AnalysisViewData:
    version: str
    libraries: List[str]
    sloc: int
    comment_ratio: float
    selected_rule: Optional[Dict]


class CodeAnalysisUseCase:
    """Application-layer analysis orchestration independent from UI widgets."""

    def __init__(self, analyzer, container_manager):
        self.analyzer = analyzer
        self.container_manager = container_manager

    def execute(self, code_text: str) -> AnalysisViewData:
        result = self.analyzer.summary(code_text)
        version = result.get("version", "Unknown")
        libraries = result.get("libraries", [])

        stream = io.BytesIO(code_text.encode("utf-8"))
        _, code, comments = count_lines_python(stream)
        ratio = (comments / (code + comments) * 100) if (code + comments) > 0 else 0.0

        selected_rule = None
        feature = self.analyzer.analyze(code_text)
        version_hint = feature.version_hint
        search_terms = feature.imports + feature.keywords
        if feature.validation_year:
            search_terms.append(f"year:{feature.validation_year}")
        selected_rule = self.container_manager.resolve_runtime(search_terms, version_hint)

        return AnalysisViewData(
            version=version,
            libraries=libraries,
            sloc=code,
            comment_ratio=ratio,
            selected_rule=selected_rule,
        )
