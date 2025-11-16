#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Service Interface and Implementation.

Provides abstraction for video recording management.
"""

from typing import Protocol, Optional, Dict, Any
from pathlib import Path
from playwright.async_api import BrowserContext


class IVideoService(Protocol):
    """Interface for video service."""
    
    def get_context_options(
        self,
        test_name: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Get browser context options for video recording."""
        ...
    
    def register_context(
        self,
        context: BrowserContext,
        test_name: Optional[str] = None
    ) -> None:
        """Register a browser context for video management."""
        ...
    
    async def pause(self, test_name: Optional[str] = None) -> None:
        """Pause video recording."""
        ...
    
    async def resume(self, test_name: Optional[str] = None) -> None:
        """Resume video recording."""
        ...
    
    async def finalize(
        self,
        test_name: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Finalize video recording and return path."""
        ...


class VideoService:
    """Video service implementation using VideoManager."""
    
    def __init__(self, video_manager):
        """
        Initialize video service.
        
        Args:
            video_manager: VideoManager instance
        """
        self._video_manager = video_manager
    
    def get_context_options(
        self,
        test_name: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Get browser context options for video recording."""
        return self._video_manager.get_context_options(
            test_name=test_name,
            viewport=viewport
        )
    
    def register_context(
        self,
        context: BrowserContext,
        test_name: Optional[str] = None
    ) -> None:
        """Register a browser context for video management."""
        self._video_manager.register_context(
            context=context,
            test_name=test_name
        )
    
    async def pause(self, test_name: Optional[str] = None) -> None:
        """Pause video recording."""
        await self._video_manager.pause(test_name=test_name)
    
    async def resume(self, test_name: Optional[str] = None) -> None:
        """Resume video recording."""
        await self._video_manager.resume(test_name=test_name)
    
    async def finalize(
        self,
        test_name: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Finalize video recording and return path."""
        return await self._video_manager.finalize(
            test_name=test_name,
            output_path=output_path
        )

