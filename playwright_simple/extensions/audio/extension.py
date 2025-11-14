#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio extension for playwright-simple.

Provides text-to-speech (TTS) functionality as an optional extension.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from ...extensions import Extension
from .config import AudioConfig
from .tts import TTSManager
from .exceptions import TTSGenerationError

logger = logging.getLogger(__name__)


class AudioExtension(Extension):
    """Extension for audio/TTS."""
    
    def __init__(self, config: AudioConfig):
        """
        Initialize audio extension.
        
        Args:
            config: Audio configuration
        """
        super().__init__('audio', {
            'enabled': config.enabled,
            'lang': config.lang,
            'engine': config.engine
        })
        self.audio_config = config
        self.audio_dir = Path(config.dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self._test_instance: Optional[Any] = None
        self._tts_manager: Optional[TTSManager] = None
    
    async def initialize(self, test_instance: Any) -> None:
        """Initialize extension with test instance."""
        self._test_instance = test_instance
        
        if self.audio_config.enabled and self.enabled:
            self._tts_manager = TTSManager(
                lang=self.audio_config.lang,
                engine=self.audio_config.engine,
                slow=self.audio_config.slow,
                voice=self.audio_config.voice,
                rate=self.audio_config.rate,
                pitch=self.audio_config.pitch,
                volume=self.audio_config.volume
            )
            logger.info("Audio extension initialized")
        else:
            logger.info("Audio extension initialized (disabled)")
    
    async def speak(self, text: str, lang: Optional[str] = None) -> Optional[Path]:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to speech
            lang: Language override
            
        Returns:
            Path to audio file or None if failed
        """
        if not self.audio_config.enabled or not self.enabled or not self._tts_manager:
            return None
        
        try:
            return await self._tts_manager.speak(text, lang)
        except TTSGenerationError as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    async def generate_audio(
        self,
        text: str,
        output_path: Path,
        lang: Optional[str] = None
    ) -> bool:
        """
        Generate audio file from text.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            lang: Language override
            
        Returns:
            True if successful, False otherwise
        """
        if not self.audio_config.enabled or not self.enabled or not self._tts_manager:
            return False
        
        try:
            return await self._tts_manager.generate_audio(text, output_path, lang)
        except TTSGenerationError as e:
            logger.error(f"TTS generation failed: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup extension resources."""
        self._tts_manager = None
        logger.info("Audio extension cleaned up")
    
    def get_yaml_actions(self) -> Dict[str, Any]:
        """Return YAML actions provided by this extension."""
        return {
            'audio.speak': self._yaml_speak,
            'audio.generate': self._yaml_generate,
        }
    
    async def _yaml_speak(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Speak text."""
        text = action_data.get('text', '')
        lang = action_data.get('lang')
        
        if not text:
            logger.warning("audio.speak: No text provided")
            return
        
        audio_path = await self.speak(text, lang)
        if audio_path:
            logger.info(f"Audio generated: {audio_path}")
        else:
            logger.warning("Failed to generate audio")
    
    async def _yaml_generate(self, test_instance: Any, action_data: Dict[str, Any]) -> None:
        """YAML action: Generate audio file."""
        text = action_data.get('text', '')
        output_path = action_data.get('output_path')
        lang = action_data.get('lang')
        
        if not text:
            logger.warning("audio.generate: No text provided")
            return
        
        if not output_path:
            logger.warning("audio.generate: No output_path provided")
            return
        
        output_path = Path(output_path)
        success = await self.generate_audio(text, output_path, lang)
        if success:
            logger.info(f"Audio generated: {output_path}")
        else:
            logger.warning(f"Failed to generate audio: {output_path}")

