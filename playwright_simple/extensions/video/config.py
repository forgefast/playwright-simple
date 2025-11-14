#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video extension configuration.

Moved from core/config.py to keep core minimal.
"""

from dataclasses import dataclass
from typing import Optional
from ...core.exceptions import ConfigurationError


@dataclass
class VideoConfig:
    """Configuration for video recording."""
    enabled: bool = True
    quality: str = "high"  # low, medium, high
    codec: str = "webm"  # webm, mp4
    dir: str = "videos"
    record_per_test: bool = True  # One video per test vs one global video
    pause_on_failure: bool = False
    speed: float = 1.0  # Video playback speed (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
    
    # Subtitle settings
    subtitles: bool = False
    hard_subtitles: bool = False
    
    # Audio/narration settings
    audio: bool = False
    narration: bool = False
    narration_lang: str = "pt-BR"
    narration_engine: str = "gtts"
    narration_slow: bool = False
    audio_file: Optional[str] = None
    audio_lang: str = "pt-BR"
    audio_engine: str = "gtts"
    audio_voice: Optional[str] = None
    audio_rate: Optional[int] = None
    audio_pitch: Optional[int] = None
    audio_volume: Optional[float] = None
    
    def __post_init__(self):
        """Validate configuration values."""
        valid_qualities = ["low", "medium", "high"]
        if self.quality not in valid_qualities:
            raise ConfigurationError(
                f"Invalid video quality: {self.quality}. Must be one of {valid_qualities}"
            )
        
        valid_codecs = ["webm", "mp4"]
        if self.codec not in valid_codecs:
            raise ConfigurationError(
                f"Invalid video codec: {self.codec}. Must be one of {valid_codecs}"
            )
        
        if self.speed <= 0:
            raise ConfigurationError(f"Video speed must be positive, got: {self.speed}")

