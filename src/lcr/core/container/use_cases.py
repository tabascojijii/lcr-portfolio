from dataclasses import dataclass
from typing import Dict, List, Optional

from lcr.core.container.generator import generate_dockerfile, save_definition


@dataclass
class BuildPreparationResult:
    config: Dict
    dockerfile_path: str
    build_args: List[str]
    tag: str
    apt_added_tools: List[str]
    has_opencv_pip_warning: bool


class EnvironmentBuildPreparationUseCase:
    """Application-layer use case for dialog-side environment build preparation."""

    def __init__(self, container_manager):
        self.container_manager = container_manager

    def prepare(self, config: Dict) -> BuildPreparationResult:
        result = dict(config)
        pip_pkgs = list(result.get("pip_packages", []))
        apt_pkgs = list(result.get("apt_packages", []))
        base_image = result.get("base_image", "")

        version = "3.6" if "3.6" in base_image else ""
        if version and self.container_manager:
            pip_pkgs = self.container_manager._apply_legacy_pins(pip_pkgs, version)
            result["pip_packages"] = pip_pkgs

        if "python3-opencv" in apt_pkgs:
            unnecessary = {"build-essential", "cmake"}
            apt_pkgs = [p for p in apt_pkgs if p not in unnecessary]
            result["apt_packages"] = apt_pkgs

        has_opencv_pip_warning = any("opencv" in p and "python" in p for p in pip_pkgs)

        apt_added_tools: List[str] = []
        if pip_pkgs and "python3-opencv" not in apt_pkgs:
            needed_tools = {"build-essential", "cmake", "python3-dev"}
            missing = sorted(list(needed_tools - set(apt_pkgs)))
            if missing:
                result.setdefault("apt_packages", []).extend(missing)
                apt_added_tools = missing

        tag = result["tag"]
        json_path = save_definition(result, tag)
        _, dockerfile_path = generate_dockerfile(str(json_path))
        build_args = self.container_manager.get_build_command(dockerfile_path, tag)

        return BuildPreparationResult(
            config=result,
            dockerfile_path=dockerfile_path,
            build_args=build_args,
            tag=tag,
            apt_added_tools=apt_added_tools,
            has_opencv_pip_warning=has_opencv_pip_warning,
        )
