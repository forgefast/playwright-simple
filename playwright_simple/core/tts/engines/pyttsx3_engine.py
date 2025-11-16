#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyttsx3 Engine implementation.

Offline TTS engine using pyttsx3 (lower quality but works offline).
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseTTSEngine
from ...exceptions import TTSGenerationError

logger = logging.getLogger(__name__)

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None


class Pyttsx3Engine(BaseTTSEngine):
    """pyttsx3 (offline TTS) engine implementation."""
    
    def is_available(self) -> bool:
        """Check if pyttsx3 is available."""
        return PYTTSX3_AVAILABLE
    
    async def generate(self, text: str, output_path: Path, lang: Optional[str] = None) -> bool:
        """Generate audio using pyttsx3 (offline, but lower quality)."""
        if not self.is_available():
            raise ImportError(
                "pyttsx3 is required for TTS. Install with: pip install pyttsx3"
            )
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._pyttsx3_sync,
                text,
                output_path
            )
            return output_path.exists()
        except Exception as e:
            logger.error(f"Error in pyttsx3 generation: {e}", exc_info=True)
            raise TTSGenerationError(f"pyttsx3 generation failed: {e}") from e
    
    def _pyttsx3_sync(self, text: str, output_path: Path):
        """Synchronous pyttsx3 generation."""
        engine = pyttsx3.init()
        
        # Configure voice (try to find Portuguese voice)
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'portuguese' in voice.name.lower() or 'pt' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Set speed (words per minute)
        engine.setProperty('rate', 150 if not self.slow else 120)
        
        # Save to file (requires pydub or similar for MP3, or use WAV)
        if output_path.suffix == '.mp3':
            # Save as WAV first, then convert
            wav_path = output_path.with_suffix('.wav')
            engine.save_to_file(text, str(wav_path))
            engine.runAndWait()
            
            # Convert WAV to MP3 using ffmpeg
            if wav_path.exists():
                subprocess.run(
                    ['ffmpeg', '-i', str(wav_path), '-y', str(output_path)],
                    capture_output=True,
                    timeout=30
                )
                wav_path.unlink()
        else:
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()

