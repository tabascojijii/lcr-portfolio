import csv
from pathlib import Path
from typing import Any, Dict, List


class LoadResultArtifactsUseCase:
    """Prepare result artifacts for UI presentation."""

    def execute(self, output_dir: str) -> Dict[str, Any]:
        out_dir = Path(output_dir)
        if not out_dir.exists():
            return {"exists": False, "images": [], "csv_previews": []}

        image_files = sorted(
            list(out_dir.glob("*.png")) + list(out_dir.glob("*.jpg")) + list(out_dir.glob("*.jpeg"))
        )
        csv_previews = [self._preview_csv(path) for path in sorted(out_dir.glob("*.csv"))]
        return {
            "exists": True,
            "images": [str(path) for path in image_files],
            "csv_previews": csv_previews,
        }

    def _preview_csv(self, csv_path: Path) -> Dict[str, Any]:
        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows: List[List[str]] = []
                for _, row in zip(range(5), reader):
                    if any(cell.strip() for cell in row):
                        rows.append(row)
            if not rows:
                return {"name": csv_path.name, "headers": [], "rows": [], "previewable": True}
            return {
                "name": csv_path.name,
                "headers": rows[0],
                "rows": rows[1:],
                "previewable": True,
            }
        except Exception:
            return {"name": csv_path.name, "headers": [], "rows": [], "previewable": False}
