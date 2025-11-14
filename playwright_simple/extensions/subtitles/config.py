#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle extension configuration.

Moved from core to keep core minimal.
"""

from dataclasses import dataclass
from ...core.exceptions import ConfigurationError


@dataclass
class SubtitleConfig:
    """Configuration for subtitles."""
    enabled: bool = False
    min_duration: float = 0.5  # Minimum duration in seconds for subtitles
    hard_subtitles: bool = False  # If True, burn subtitles into video (slower but always visible)
    style: str = "default"  # Subtitle style (default, large, small, etc.)
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.min_duration < 0:
            raise ConfigurationError(
                f"Subtitle min_duration must be >= 0, got: {self.min_duration}"
            )

