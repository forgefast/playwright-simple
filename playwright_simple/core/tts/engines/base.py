#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base TTS Engine class.

Provides abstract interface for TTS engine implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseTTSEngine(ABC):
    """Base class for TTS engine implementations."""
    
    def __init__(
        self,
        lang: str = 'pt-br',
        slow: bool = False,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None
    ):
        """
        Initialize TTS engine.
        
        Args:
            lang: Language code (pt-br, en, es, etc.)
            slow: Whether to speak slowly (engine-specific)
            voice: Specific voice name/ID (engine-specific)
            rate: Speech rate (engine-specific)
            pitch: Voice pitch (engine-specific)
            volume: Voice volume (engine-specific)
        """
        self.lang = lang
        self.slow = slow
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
    
    @abstractmethod
    async def generate(self, text: str, output_path: Path, lang: Optional[str] = None) -> bool:
        """
        Generate audio file from text.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            lang: Language override (uses self.lang if None)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            TTSGenerationError: If generation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this engine is available (library installed).
        
        Returns:
            True if engine is available, False otherwise
        """
        pass

