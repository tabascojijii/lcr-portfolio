# src/lcr/core/interface.py

from abc import ABC, abstractmethod
from typing import Dict, Optional


class EraStrategyInterface(ABC):
    """
    Abstract interface for era-specific compatibility detection strategies.
    
    Each concrete strategy (e.g., Python27Strategy, Python36Strategy) implements
    methods to detect if a given code is compatible with a specific environment
    and provides the appropriate Docker image for execution.
    
    This follows the Strategy Pattern to allow flexible, extensible era detection.
    """

    @abstractmethod
    def detect_compatibility(self, code_text: str) -> Dict[str, any]:
        """
        Analyze code and determine compatibility with this era's environment.
        
        Args:
            code_text (str): Source code to analyze
        
        Returns:
            dict: Compatibility information with the following structure:
                {
                    "compatible": bool,           # True if code is compatible
                    "confidence": float,          # Confidence score (0.0 to 1.0)
                    "indicators": list[str],      # Detected compatibility indicators
                    "warnings": list[str]         # Potential compatibility issues
                }
        
        Example:
            >>> strategy = Python27Strategy()
            >>> result = strategy.detect_compatibility("print 'Hello'")
            >>> result["compatible"]
            True
        """
        raise NotImplementedError

    @abstractmethod
    def get_docker_image(self) -> str:
        """
        Get the Docker image tag for this era's environment.
        
        Returns:
            str: Docker image tag (e.g., "python:2.7", "python:3.6")
        
        Example:
            >>> strategy = Python27Strategy()
            >>> strategy.get_docker_image()
            'python:2.7'
        """
        raise NotImplementedError

    @property
    def era_name(self) -> str:
        """
        Get the human-readable name of this era.
        
        Returns:
            str: Era name (e.g., "Python 2.7", "Python 3.6")
        """
        return "Unknown Era"

    @property
    def description(self) -> str:
        """
        Get a brief description of this era's environment.
        
        Returns:
            str: Description of the environment
        """
        return ""
