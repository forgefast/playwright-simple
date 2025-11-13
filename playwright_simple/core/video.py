#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video recording management system for playwright-simple.

Handles video recording with quality, codec, and pause/resume support.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext, Page

from .config import VideoConfig


class VideoManager:
    """Manages video recording."""
    
    def __init__(self, config: VideoConfig):
        """
        Initialize video manager.
        
        Args:
            config: Video configuration
        """
        self.config = config
        self.video_dir = Path(config.dir)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self._recording_contexts: Dict[str, BrowserContext] = {}
        self._paused_contexts: set = set()
    
    def get_context_options(self, test_name: Optional[str] = None, viewport: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Get browser context options for video recording.
        
        Args:
            test_name: Name of test (for video filename)
            viewport: Viewport size from browser config (if provided, use this for video size)
            
        Returns:
            Dictionary of context options
        """
        if not self.config.enabled:
            return {}
        
        # Use viewport size if provided, otherwise fall back to quality mapping
        # This ensures video size matches viewport size (prevents cropping)
        if viewport:
            video_size = viewport
        else:
            # Map quality to video size (fallback)
            quality_map = {
                "low": {"width": 1280, "height": 720},
                "medium": {"width": 1920, "height": 1080},
                "high": {"width": 1920, "height": 1080},  # Changed from 2560x1440 to match common viewport
            }
            video_size = quality_map.get(self.config.quality, quality_map["high"])
        
        # Use record_video_dir - Playwright will create video with hash, we'll rename after
        # Always use the main video_dir (no subdirectories in the path)
        # IMPORTANT: record_video_size must match viewport size to prevent cropping
        return {
            "record_video_dir": str(self.video_dir),
            "record_video_size": video_size,
        }
    
    def register_context(self, context: BrowserContext, test_name: Optional[str] = None):
        """
        Register a browser context for video management.
        
        Args:
            context: Browser context
            test_name: Name of test using this context
        """
        if test_name:
            self._recording_contexts[test_name] = context
    
    async def pause(self, test_name: Optional[str] = None):
        """
        Pause video recording.
        
        Args:
            test_name: Name of test (if None, pauses all)
        """
        if not self.config.enabled:
            return
        
        if test_name:
            if test_name in self._recording_contexts:
                context = self._recording_contexts[test_name]
                # Note: Playwright doesn't have direct pause, but we can track it
                self._paused_contexts.add(test_name)
        else:
            # Pause all
            self._paused_contexts.update(self._recording_contexts.keys())
    
    async def resume(self, test_name: Optional[str] = None):
        """
        Resume video recording.
        
        Args:
            test_name: Name of test (if None, resumes all)
        """
        if not self.config.enabled:
            return
        
        if test_name:
            self._paused_contexts.discard(test_name)
        else:
            self._paused_contexts.clear()
    
    def is_paused(self, test_name: Optional[str] = None) -> bool:
        """
        Check if recording is paused.
        
        Args:
            test_name: Name of test (if None, checks if any are paused)
            
        Returns:
            True if paused
        """
        if test_name:
            return test_name in self._paused_contexts
        return len(self._paused_contexts) > 0
    
    async def stop_all(self):
        """Stop all video recordings."""
        # Close all registered contexts (which will finalize videos)
        for context in self._recording_contexts.values():
            try:
                await context.close()
            except Exception:
                pass
        self._recording_contexts.clear()
        self._paused_contexts.clear()
    
    def get_video_path(self, test_name: str) -> Optional[Path]:
        """
        Get path to video file for a test.
        
        Args:
            test_name: Name of test
            
        Returns:
            Path to video file if exists, None otherwise
        """
        if not self.config.enabled:
            return None
        
        # Check for video with test name directly in video_dir (no subdirectories)
        video_extensions = ['.webm', '.mp4']
        for ext in video_extensions:
            video_file = self.video_dir / f"{test_name}{ext}"
            if video_file.exists():
                return video_file
        
        # Fallback: look for any video file with test name in it (in case of conflicts)
        for ext in video_extensions:
            video_files = list(self.video_dir.glob(f"{test_name}*{ext}"))
            if video_files:
                return video_files[0]  # Return first found
        
        return None



