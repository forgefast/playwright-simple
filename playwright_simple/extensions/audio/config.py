#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio extension configuration.

Moved from core/config.py to keep core minimal.
"""

from dataclasses import dataclass
from typing import Optional
from ...core.exceptions import ConfigurationError


@dataclass
class AudioConfig:
    """Configuration for audio/TTS."""
    enabled: bool = False
    lang: str = 'pt-br'  # Language code (pt-br, en, es, etc.)
    engine: str = 'edge-tts'  # TTS engine ('gtts', 'edge-tts', or 'pyttsx3')
    slow: bool = False  # Whether to speak slowly (gTTS only)
    voice: Optional[str] = None  # Specific voice name/ID
    rate: Optional[str] = None  # Speech rate for edge-tts
    pitch: Optional[str] = None  # Voice pitch for edge-tts
    volume: Optional[str] = None  # Voice volume for edge-tts
    dir: str = "audio"  # Directory to save audio files
    
    def __post_init__(self):
        """Validate configuration values."""
        valid_engines = ["gtts", "edge-tts", "pyttsx3"]
        if self.engine not in valid_engines:
            raise ConfigurationError(
                f"Invalid TTS engine: {self.engine}. Must be one of {valid_engines}"
            )

