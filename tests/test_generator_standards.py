import pytest

from lcr.core.container.generator import render_dockerfile


def test_render_dockerfile_requires_digest_pinned_base_image():
    with pytest.raises(ValueError):
        render_dockerfile({"base_image": "python:3.10-slim"})


def test_render_dockerfile_uses_multistage_and_constraints():
    dockerfile = render_dockerfile(
        {
            "base_image": "python:3.10-slim@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "pip_packages": ["numpy==1.23.5"],
        }
    )
    assert "AS builder" in dockerfile
    assert "AS runtime" in dockerfile
    assert "COPY constraints.txt" in dockerfile
    assert "-c /tmp/build/constraints.txt" in dockerfile
