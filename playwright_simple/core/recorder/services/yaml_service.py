#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML Service Interface and Implementation.

Provides abstraction for YAML reading and writing.
"""

from typing import Protocol, Optional, Dict, Any, List
from pathlib import Path


class IYAMLService(Protocol):
    """Interface for YAML service."""
    
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the YAML."""
        ...
    
    def add_caption(self, text: str) -> None:
        """Add caption/subtitle step."""
        ...
    
    def add_subtitle_to_last_step(self, text: str) -> None:
        """Add subtitle to the last step."""
        ...
    
    def add_audio_to_last_step(self, text: str) -> None:
        """Add audio to the last step."""
        ...
    
    def set_metadata(self, name: str, description: str) -> None:
        """Set YAML metadata."""
        ...
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set YAML configuration."""
        ...
    
    def save(self) -> None:
        """Save YAML to file."""
        ...
    
    def load(self) -> Dict[str, Any]:
        """Load YAML from file."""
        ...
    
    @property
    def steps(self) -> List[Dict[str, Any]]:
        """Get YAML steps."""
        ...


class YAMLService:
    """YAML service implementation using YAMLWriter."""
    
    def __init__(self, yaml_writer=None, yaml_path: Optional[Path] = None):
        """
        Initialize YAML service.
        
        Args:
            yaml_writer: YAMLWriter instance (for write mode)
            yaml_path: Path to YAML file (for read mode)
        """
        self._yaml_writer = yaml_writer
        self._yaml_path = yaml_path
        self._yaml_data: Optional[Dict[str, Any]] = None
    
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the YAML."""
        if self._yaml_writer:
            self._yaml_writer.add_step(step)
    
    def add_caption(self, text: str) -> None:
        """Add caption/subtitle step."""
        if self._yaml_writer:
            self._yaml_writer.add_caption(text)
    
    def add_subtitle_to_last_step(self, text: str) -> None:
        """Add subtitle to the last step."""
        if self._yaml_writer:
            self._yaml_writer.add_subtitle_to_last_step(text)
    
    def add_audio_to_last_step(self, text: str) -> None:
        """Add audio to the last step."""
        if self._yaml_writer:
            self._yaml_writer.add_audio_to_last_step(text)
    
    def set_metadata(self, name: str, description: str) -> None:
        """Set YAML metadata."""
        if self._yaml_writer:
            self._yaml_writer.metadata['name'] = name
            self._yaml_writer.metadata['description'] = description
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set YAML configuration."""
        if self._yaml_writer:
            self._yaml_writer.config = config
    
    def save(self) -> None:
        """Save YAML to file."""
        if self._yaml_writer:
            self._yaml_writer.save()
    
    def load(self) -> Dict[str, Any]:
        """Load YAML from file."""
        if self._yaml_data is not None:
            return self._yaml_data
        
        if self._yaml_path and self._yaml_path.exists():
            import yaml
            with open(self._yaml_path, 'r', encoding='utf-8') as f:
                self._yaml_data = yaml.safe_load(f)
            return self._yaml_data or {}
        
        return {}
    
    @property
    def steps(self) -> List[Dict[str, Any]]:
        """Get YAML steps."""
        if self._yaml_writer:
            return self._yaml_writer.steps
        elif self._yaml_data:
            return self._yaml_data.get('steps', [])
        return []

