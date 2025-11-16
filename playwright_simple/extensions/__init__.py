#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extensions system for playwright-simple.

Extensions provide optional functionality like video recording, audio narration,
subtitles, accessibility analysis, etc.

Core principle: Extensions are optional and pluggable. The core library works
without any extensions, but you can add them as needed.
"""

import logging
from typing import Protocol, Optional, Any, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

__all__ = ['Extension', 'ExtensionRegistry']


class Extension(ABC):
    """Base class for all extensions."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize extension.
        
        Args:
            name: Extension name (e.g., 'video', 'audio', 'subtitles')
            config: Extension-specific configuration
        """
        self.name = name
        self.config = config or {}
        self._enabled = True
    
    @property
    def enabled(self) -> bool:
        """Check if extension is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the extension."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the extension."""
        self._enabled = False
    
    async def initialize(self, test_instance: Any) -> None:
        """
        Initialize extension with test instance.
        
        Called when extension is registered with a test instance.
        
        Args:
            test_instance: The test instance (SimpleTestBase or subclass)
        """
        pass
    
    async def cleanup(self) -> None:
        """Cleanup extension resources."""
        pass
    
    def get_yaml_actions(self) -> Dict[str, Any]:
        """
        Return YAML actions that this extension provides.
        
        Returns:
            Dictionary mapping action names to action handlers
            Example: {'video.start_recording': self.start_recording}
        """
        return {}


class ExtensionRegistry:
    """Registry for managing extensions."""
    
    def __init__(self):
        """Initialize extension registry."""
        self._extensions: Dict[str, Extension] = {}
        self._test_instance: Optional[Any] = None
    
    def register(self, extension: Extension) -> None:
        """
        Register an extension.
        
        Args:
            extension: Extension instance to register
        """
        self._extensions[extension.name] = extension
        logger.info(f"Extension '{extension.name}' registered")
    
    def unregister(self, name: str) -> None:
        """
        Unregister an extension.
        
        Args:
            name: Extension name
        """
        if name in self._extensions:
            del self._extensions[name]
            logger.info(f"Extension '{name}' unregistered")
    
    def get(self, name: str) -> Optional[Extension]:
        """
        Get extension by name.
        
        Args:
            name: Extension name
            
        Returns:
            Extension instance or None if not found
        """
        return self._extensions.get(name)
    
    def has(self, name: str) -> bool:
        """
        Check if extension is registered.
        
        Args:
            name: Extension name
            
        Returns:
            True if extension is registered
        """
        return name in self._extensions
    
    async def initialize_all(self, test_instance: Any) -> None:
        """
        Initialize all registered extensions.
        
        Args:
            test_instance: Test instance to pass to extensions
        """
        self._test_instance = test_instance
        for extension in self._extensions.values():
            if extension.enabled:
                await extension.initialize(test_instance)
    
    async def cleanup_all(self) -> None:
        """Cleanup all registered extensions."""
        for extension in self._extensions.values():
            if extension.enabled:
                await extension.cleanup()
    
    def get_all_yaml_actions(self) -> Dict[str, Any]:
        """
        Get all YAML actions from all extensions.
        
        Returns:
            Dictionary mapping action names to handlers
        """
        actions = {}
        for extension in self._extensions.values():
            if extension.enabled:
                actions.update(extension.get_yaml_actions())
        return actions
    
    def list_extensions(self) -> list[str]:
        """
        List all registered extension names.
        
        Returns:
            List of extension names
        """
        return list(self._extensions.keys())


# Import logger
import logging
logger = logging.getLogger(__name__)

# Make ExtensionRegistry available at package level
__all__ = ['Extension', 'ExtensionRegistry']

