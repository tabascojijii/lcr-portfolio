from pathlib import Path
import re


def test_generated_dockerfiles_use_digest_pinned_from():
    image_dir = Path("src/lcr/core/container/images")
    dockerfiles = sorted(image_dir.glob("Dockerfile.*"))
    assert dockerfiles, "No generated Dockerfiles found under src/lcr/core/container/images"

    pattern = re.compile(r"^FROM\s+.+@sha256:[0-9a-f]{64}(?:\s+AS\s+\w+)?\s*$")
    violations = []

    for dockerfile in dockerfiles:
        first_line = dockerfile.read_text(encoding="utf-8").splitlines()[0].strip()
        if not pattern.match(first_line):
            violations.append(f"{dockerfile}: {first_line}")

    assert not violations, "Digest pinning violations:\n" + "\n".join(violations)
