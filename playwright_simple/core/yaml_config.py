#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML configuration management.

Handles applying configuration from YAML files to test instances.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .logger import get_logger, set_logger, StructuredLogger

logger = logging.getLogger(__name__)


class YAMLConfigManager:
    """Manages configuration from YAML files."""
    
    @staticmethod
    def apply_config(config_data: Dict[str, Any], test: Any) -> None:
        """
        Apply configuration from YAML to test instance.
        
        Args:
            config_data: Configuration dictionary from YAML
            test: Test base instance to configure
        """
        if not config_data:
            return
        
        # Apply logging config first
        if 'logging' in config_data:
            YAMLConfigManager._apply_logging_config(config_data['logging'])
        
        # Apply cursor config
        if 'cursor' in config_data:
            YAMLConfigManager._apply_cursor_config(config_data['cursor'], test)
        
        # Apply video config
        if 'video' in config_data:
            YAMLConfigManager._apply_video_config(config_data['video'], test)
        
        # Apply browser config
        if 'browser' in config_data:
            YAMLConfigManager._apply_browser_config(config_data['browser'], test)
    
    @staticmethod
    def _apply_logging_config(logging_data: Dict[str, Any]) -> None:
        """Apply logging configuration."""
        log_file = Path(logging_data.get('log_file')) if logging_data.get('log_file') else None
        logger_instance = StructuredLogger(
            name="playwright_simple",
            level=logging_data.get('level', 'INFO'),
            log_file=log_file,
            json_log=logging_data.get('json_log', False),
            console_output=logging_data.get('console_output', True)
        )
        set_logger(logger_instance)
    
    @staticmethod
    def _apply_cursor_config(cursor_data: Dict[str, Any], test: Any) -> None:
        """Apply cursor configuration."""
        if 'style' in cursor_data:
            test.config.cursor.style = cursor_data['style']
        if 'color' in cursor_data:
            test.config.cursor.color = cursor_data['color']
        if 'size' in cursor_data:
            test.config.cursor.size = cursor_data['size']
        if 'click_effect' in cursor_data:
            test.config.cursor.click_effect = cursor_data['click_effect']
        if 'animation_speed' in cursor_data:
            test.config.cursor.animation_speed = cursor_data['animation_speed']
    
    @staticmethod
    def _apply_video_config(video_data: Dict[str, Any], test: Any) -> None:
        """Apply video configuration."""
        if 'enabled' in video_data:
            test.config.video.enabled = video_data['enabled']
        if 'quality' in video_data:
            test.config.video.quality = video_data['quality']
        if 'codec' in video_data:
            test.config.video.codec = video_data['codec']
        if 'speed' in video_data:
            test.config.video.speed = float(video_data['speed'])
        if 'subtitles' in video_data:
            test.config.video.subtitles = bool(video_data['subtitles'])
        if 'hard_subtitles' in video_data:
            test.config.video.hard_subtitles = bool(video_data['hard_subtitles'])
        if 'audio' in video_data:
            test.config.video.audio = bool(video_data['audio'])
        if 'narration' in video_data:
            test.config.video.narration = bool(video_data['narration'])
        if 'narration_lang' in video_data:
            test.config.video.narration_lang = video_data['narration_lang']
        if 'narration_engine' in video_data:
            test.config.video.narration_engine = video_data['narration_engine']
        if 'narration_slow' in video_data:
            test.config.video.narration_slow = bool(video_data['narration_slow'])
        if 'audio_file' in video_data:
            test.config.video.audio_file = video_data['audio_file']
        if 'audio_lang' in video_data:
            test.config.video.audio_lang = video_data['audio_lang']
        if 'audio_engine' in video_data:
            test.config.video.audio_engine = video_data['audio_engine']
        if 'audio_voice' in video_data:
            test.config.video.audio_voice = video_data['audio_voice']
        if 'audio_rate' in video_data:
            test.config.video.audio_rate = video_data['audio_rate']
        if 'audio_pitch' in video_data:
            test.config.video.audio_pitch = video_data['audio_pitch']
        if 'audio_volume' in video_data:
            test.config.video.audio_volume = video_data['audio_volume']
    
    @staticmethod
    def _apply_browser_config(browser_data: Dict[str, Any], test: Any) -> None:
        """Apply browser configuration."""
        if 'headless' in browser_data:
            test.config.browser.headless = browser_data['headless']
        if 'slow_mo' in browser_data:
            test.config.browser.slow_mo = browser_data['slow_mo']

