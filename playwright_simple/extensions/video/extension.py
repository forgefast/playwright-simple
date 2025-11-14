#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video extension for playwright-simple.

Provides video recording functionality as an optional extension.
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext

from ...extensions import Extension
from .config import VideoConfig

logger = logging.getLogger(__name__)


class VideoExtension(Extension):
    """Extension for video recording."""
    
    def __init__(self, config: VideoConfig):
        """
        Initialize video extension.
        
        Args:
            config: Video configuration
        """
        super().__init__('video', {'enabled': config.enabled, 'quality': config.quality, 'dir': config.dir})
        self.video_config = config
        self.video_dir = Path(config.dir)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self._recording_contexts: Dict[str, BrowserContext] = {}
        self._paused_contexts: set = set()
        self._test_instance: Optional[Any] = None
    
    async def initialize(self, test_instance: Any) -> None:
        """Initialize extension with test instance."""
        self._test_instance = test_instance
        logger.info("Video extension initialized")
    
    def get_context_options(
        self, 
        test_name: Optional[str] = None, 
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Get browser context options for video recording.
        
        Args:
            test_name: Name of test (for video filename)
            viewport: Viewport size from browser config
            
        Returns:
            Dictionary of context options
        """
        if not self.video_config.enabled or not self.enabled:
            return {}
        
        # Use viewport size if provided, otherwise fall back to quality mapping
        if viewport:
            video_size = viewport
        else:
            quality_map = {
                "low": {"width": 1280, "height": 720},
                "medium": {"width": 1920, "height": 1080},
                "high": {"width": 1920, "height": 1080},
            }
            video_size = quality_map.get(self.video_config.quality, quality_map["high"])
        
        return {
            "record_video_dir": str(self.video_dir),
            "record_video_size": video_size,
        }
    
    def register_context(
        self, 
        context: BrowserContext, 
        test_name: Optional[str] = None
    ) -> None:
        """Register a browser context for video management."""
        if test_name:
            self._recording_contexts[test_name] = context
    
    async def pause(self, test_name: Optional[str] = None) -> None:
        """Pause video recording."""
        if not self.video_config.enabled or not self.enabled:
            return
        
        if test_name:
            if test_name in self._recording_contexts:
                self._paused_contexts.add(test_name)
        else:
            self._paused_contexts.update(self._recording_contexts.keys())
    
    async def resume(self, test_name: Optional[str] = None) -> None:
        """Resume video recording."""
        if not self.video_config.enabled or not self.enabled:
            return
        
        if test_name:
            self._paused_contexts.discard(test_name)
        else:
            self._paused_contexts.clear()
    
    def is_paused(self, test_name: Optional[str] = None) -> bool:
        """Check if recording is paused."""
        if test_name:
            return test_name in self._paused_contexts
        return len(self._paused_contexts) > 0
    
    async def cleanup(self) -> None:
        """Stop all video recordings."""
        for context in self._recording_contexts.values():
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing video context: {e}")
        self._recording_contexts.clear()
        self._paused_contexts.clear()
    
    def get_video_path(self, test_name: str) -> Optional[Path]:
        """Get path to video file for a test."""
        if not self.video_config.enabled or not self.enabled:
            return None
        
        video_extensions = ['.webm', '.mp4']
        for ext in video_extensions:
            video_file = self.video_dir / f"{test_name}{ext}"
            if video_file.exists():
                return video_file
        
        for ext in video_extensions:
            video_files = list(self.video_dir.glob(f"{test_name}*{ext}"))
            if video_files:
                return video_files[0]
        
        return None
    
    def get_yaml_actions(self) -> Dict[str, Any]:
        """Return YAML actions provided by this extension."""
        return {
            'video.start_recording': self._yaml_start_recording,
            'video.stop_recording': self._yaml_stop_recording,
            'video.pause': self._yaml_pause,
            'video.resume': self._yaml_resume,
        }
    
    async def _yaml_start_recording(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Start video recording."""
        test_name = action_data.get('test_name') or getattr(test_instance, 'test_name', 'test')
        if self._test_instance and hasattr(self._test_instance, 'context'):
            self.register_context(self._test_instance.context, test_name)
        logger.info(f"Video recording started for test: {test_name}")
    
    async def _yaml_stop_recording(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Stop video recording."""
        await self.cleanup()
        logger.info("Video recording stopped")
    
    async def _yaml_pause(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Pause video recording."""
        test_name = action_data.get('test_name')
        await self.pause(test_name)
        logger.info(f"Video recording paused for test: {test_name or 'all'}")
    
    async def _yaml_resume(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Resume video recording."""
        test_name = action_data.get('test_name')
        await self.resume(test_name)
        logger.info(f"Video recording resumed for test: {test_name or 'all'}")
    
    def validate_video(self, video_path: Path, test_duration: Optional[float] = None) -> Dict[str, Any]:
        """
        Validate video file integrity and requirements.
        
        Args:
            video_path: Path to video file
            test_duration: Expected test duration in seconds (for comparison)
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'valid': False,
            'exists': False,
            'playable': False,
            'size_ok': False,
            'duration_ok': False,
            'errors': [],
            'warnings': []
        }
        
        if not video_path.exists():
            validation['errors'].append('Video file does not exist')
            return validation
        
        validation['exists'] = True
        
        # Check file size (should not be empty)
        try:
            size = video_path.stat().st_size
            if size == 0:
                validation['errors'].append('Video file is empty (0 bytes)')
                return validation
            validation['size_ok'] = True
            if size < 1024:  # Less than 1KB is suspicious
                validation['warnings'].append(f'Video file is very small ({size} bytes)')
        except Exception as e:
            validation['errors'].append(f'Error checking file size: {e}')
            return validation
        
        # Try to get video info using ffprobe
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration,size',
                '-of', 'json',
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                format_info = data.get('format', {})
                duration = float(format_info.get('duration', 0))
                
                validation['playable'] = True
                
                # Compare duration with test duration if provided
                if test_duration is not None:
                    # Allow some tolerance (video might be slightly shorter due to processing)
                    if duration >= test_duration * 0.8:  # At least 80% of test duration
                        validation['duration_ok'] = True
                    else:
                        validation['warnings'].append(
                            f'Video duration ({duration:.2f}s) is much shorter than test duration ({test_duration:.2f}s)'
                        )
                else:
                    validation['duration_ok'] = True
                
                validation['valid'] = True
            else:
                validation['errors'].append(f'Video file appears corrupted: {result.stderr[:200]}')
                
        except subprocess.TimeoutExpired:
            validation['errors'].append('Timeout validating video file')
        except FileNotFoundError:
            validation['warnings'].append('ffprobe not found, skipping video validation')
            # If ffprobe is not available, assume valid if file exists and has size
            validation['valid'] = validation['size_ok']
        except Exception as e:
            validation['errors'].append(f'Error validating video: {e}')
        
        return validation

