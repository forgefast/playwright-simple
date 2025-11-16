#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle extension for playwright-simple.

Provides subtitle generation functionality as an optional extension.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...extensions import Extension
from .config import SubtitleConfig
from .generator import SubtitleGenerator

logger = logging.getLogger(__name__)


class SubtitleExtension(Extension):
    """Extension for subtitle generation."""
    
    def __init__(self, config: SubtitleConfig):
        """
        Initialize subtitle extension.
        
        Args:
            config: Subtitle configuration
        """
        super().__init__('subtitles', {
            'enabled': config.enabled,
            'hard_subtitles': config.hard_subtitles
        })
        self.subtitle_config = config
        self._test_instance: Optional[Any] = None
        self._generator: Optional[SubtitleGenerator] = None
    
    async def initialize(self, test_instance: Any) -> None:
        """Initialize extension with test instance."""
        self._test_instance = test_instance
        
        if self.subtitle_config.enabled and self.enabled:
            self._generator = SubtitleGenerator(self.subtitle_config)
            logger.info("Subtitle extension initialized")
        else:
            logger.info("Subtitle extension initialized (disabled)")
    
    async def generate(
        self,
        video_path: Path,
        test_steps: List[Any],
        start_time: datetime
    ) -> Optional[Path]:
        """
        Generate SRT subtitle file from test steps.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps
            start_time: Video start time
            
        Returns:
            Path to SRT file or None if failed
        """
        if not self.subtitle_config.enabled or not self.enabled or not self._generator:
            return None
        
        return await self._generator.generate(video_path, test_steps, start_time)
    
    async def embed(self, video_path: Path, srt_path: Path) -> Optional[Path]:
        """
        Embed subtitles into video.
        
        Args:
            video_path: Path to video file
            srt_path: Path to SRT file
            
        Returns:
            Path to video with subtitles or original path
        """
        if not self.subtitle_config.enabled or not self.enabled or not self._generator:
            return video_path
        
        return await self._generator.embed(video_path, srt_path)
    
    async def cleanup(self) -> None:
        """Cleanup extension resources."""
        self._generator = None
        logger.info("Subtitle extension cleaned up")
    
    def get_yaml_actions(self) -> Dict[str, Any]:
        """Return YAML actions provided by this extension."""
        return {
            'subtitles.generate': self._yaml_generate,
            'subtitles.embed': self._yaml_embed,
        }
    
    async def _yaml_generate(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Generate subtitles."""
        video_path = action_data.get('video_path')
        test_steps = action_data.get('test_steps', [])
        start_time = action_data.get('start_time')
        
        if not video_path:
            logger.warning("subtitles.generate: No video_path provided")
            return
        
        video_path = Path(video_path)
        if not start_time:
            from datetime import datetime
            start_time = datetime.now()
        
        srt_path = await self.generate(video_path, test_steps, start_time)
        if srt_path:
            logger.info(f"Subtitles generated: {srt_path}")
        else:
            logger.warning("Failed to generate subtitles")
    
    async def _yaml_embed(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Embed subtitles in video."""
        video_path = action_data.get('video_path')
        srt_path = action_data.get('srt_path')
        
        if not video_path:
            logger.warning("subtitles.embed: No video_path provided")
            return
        
        if not srt_path:
            logger.warning("subtitles.embed: No srt_path provided")
            return
        
        video_path = Path(video_path)
        srt_path = Path(srt_path)
        
        result = await self.embed(video_path, srt_path)
        if result:
            logger.info(f"Subtitles embedded: {result}")
        else:
            logger.warning("Failed to embed subtitles")

