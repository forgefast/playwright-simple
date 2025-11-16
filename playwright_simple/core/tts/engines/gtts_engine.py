#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gTTS Engine implementation.

Google Text-to-Speech engine for TTS generation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .base import BaseTTSEngine
from ...exceptions import TTSGenerationError

logger = logging.getLogger(__name__)

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None


class GTTSEngine(BaseTTSEngine):
    """gTTS (Google Text-to-Speech) engine implementation."""
    
    def is_available(self) -> bool:
        """Check if gTTS is available."""
        return GTTS_AVAILABLE
    
    async def generate(self, text: str, output_path: Path, lang: Optional[str] = None) -> bool:
        """Generate audio using gTTS (Google Text-to-Speech)."""
        if not self.is_available():
            raise ImportError(
                "gTTS is required for TTS. Install with: pip install gtts"
            )
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._gtts_sync,
                text,
                output_path,
                lang or self.lang
            )
            return output_path.exists()
        except Exception as e:
            logger.error(f"Error in gTTS generation: {e}", exc_info=True)
            raise TTSGenerationError(f"gTTS generation failed: {e}") from e
    
    def _gtts_sync(self, text: str, output_path: Path, lang: str):
        """Synchronous gTTS generation."""
        tts = gTTS(text=text, lang=lang, slow=self.slow)
        tts.save(str(output_path))

