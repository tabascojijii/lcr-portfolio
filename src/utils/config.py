# src/lcr/utils/config.py

import json
import os
from pathlib import Path


class LCRConfig:
    """
    Legacy Code Reviver configuration manager.
    Handles Docker image management and path conversion for container execution.
    """
    
    # Default Docker images for common legacy environments
    DEFAULT_IMAGES = [
        {"name": "Python 2.7", "image": "python:2.7", "description": "Legacy Python 2.7 environment"},
        {"name": "Python 3.6", "image": "python:3.6", "description": "Python 3.6 (EOL 2021)"},
        {"name": "Python 3.8", "image": "python:3.8", "description": "Python 3.8"},
        {"name": "Ubuntu 16.04", "image": "ubuntu:16.04", "description": "Ubuntu 16.04 LTS (Xenial)"},
    ]
    
    def __init__(self, config_path="lcr_config.json"):
        """
        Initialize LCRConfig.
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file, or return default config if not exists."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Default LCR configuration
            return {
                "docker_images": self.DEFAULT_IMAGES,
                "mount_settings": {
                    "default_work_dir": "/workspace",
                    "mount_mode": "rw",  # read-write
                },
                "execution_settings": {
                    "auto_remove_container": True,
                    "timeout_seconds": 300,
                }
            }

    def save_config(self):
        """Save current configuration to file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_docker_images(self):
        """
        Get list of available Docker images.
        
        Returns:
            list: List of Docker image configurations
        """
        return self.config.get("docker_images", self.DEFAULT_IMAGES)

    def add_docker_image(self, name, image, description=""):
        """
        Add a new Docker image to the configuration.
        
        Args:
            name (str): Display name for the image
            image (str): Docker image tag (e.g., "python:2.7")
            description (str): Optional description
        """
        images = self.config.get("docker_images", [])
        images.append({
            "name": name,
            "image": image,
            "description": description
        })
        self.config["docker_images"] = images
        self.save_config()

    def get_default_work_dir(self):
        """
        Get the default working directory inside containers.
        
        Returns:
            str: Default work directory path (e.g., "/workspace")
        """
        return self.config.get("mount_settings", {}).get("default_work_dir", "/workspace")

    def set_default_work_dir(self, work_dir):
        """
        Set the default working directory for containers.
        
        Args:
            work_dir (str): Container work directory path
        """
        if "mount_settings" not in self.config:
            self.config["mount_settings"] = {}
        self.config["mount_settings"]["default_work_dir"] = work_dir
        self.save_config()

    def to_container_path(self, host_path, work_dir=None):
        """
        Convert a host absolute path to its corresponding container mount path.
        
        This method assumes the host directory is mounted to work_dir in the container.
        For example, if /host/project/script.py is in /host/project and work_dir is /workspace,
        then script.py will be accessible at /workspace/script.py in the container.
        
        Args:
            host_path (str): Absolute path on the host system
            work_dir (str): Container working directory (uses default if None)
        
        Returns:
            str: Corresponding path inside the container
        
        Example:
            >>> config = LCRConfig()
            >>> config.to_container_path("/home/user/project/script.py")
            '/workspace/script.py'
        """
        if work_dir is None:
            work_dir = self.get_default_work_dir()
        
        # Get the filename from the host path
        filename = os.path.basename(host_path)
        
        # In LCR's model, we mount the directory containing the script
        # So the script is always at {work_dir}/{filename}
        container_path = f"{work_dir}/{filename}"
        
        return container_path

    def get_mount_mode(self):
        """
        Get the mount mode for volume mounts.
        
        Returns:
            str: Mount mode ("rw" for read-write, "ro" for read-only)
        """
        return self.config.get("mount_settings", {}).get("mount_mode", "rw")

    def get_auto_remove_setting(self):
        """
        Check if containers should be automatically removed after execution.
        
        Returns:
            bool: True if auto-remove is enabled
        """
        return self.config.get("execution_settings", {}).get("auto_remove_container", True)

    def get_timeout(self):
        """
        Get the execution timeout in seconds.
        
        Returns:
            int: Timeout in seconds (0 means no timeout)
        """
        return self.config.get("execution_settings", {}).get("timeout_seconds", 300)
