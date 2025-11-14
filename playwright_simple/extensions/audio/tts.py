#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-to-Speech (TTS) implementation for audio extension.

Moved from core/tts.py to keep core minimal.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
import subprocess

from .exceptions import TTSGenerationError

logger = logging.getLogger(__name__)

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSManager:
    """Manages text-to-speech generation for test narration."""
    
    def __init__(self, lang: str = 'pt-br', engine: str = 'gtts', slow: bool = False, voice: Optional[str] = None,
                 rate: Optional[str] = None, pitch: Optional[str] = None, volume: Optional[str] = None):
        """
        Initialize TTS manager.
        
        Args:
            lang: Language code (pt-br, en, es, etc.)
            engine: TTS engine to use ('gtts', 'edge-tts', or 'pyttsx3')
            slow: Whether to speak slowly (gTTS only, ignored for other engines)
            voice: Specific voice name/ID (for edge-tts: e.g., 'pt-BR-FranciscaNeural', for pyttsx3: voice ID)
            rate: Speech rate for edge-tts: 'x-slow', 'slow', 'medium', 'fast', 'x-fast', or percentage like '+20%', '-10%'
            pitch: Voice pitch for edge-tts: 'x-low', 'low', 'medium', 'high', 'x-high', or Hz like '+50Hz', '-20Hz'
            volume: Voice volume for edge-tts: 'silent', 'x-soft', 'soft', 'medium', 'loud', 'x-loud'
        """
        self.lang = lang
        self.engine = engine
        self.slow = slow
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        
        if engine == 'gtts' and not GTTS_AVAILABLE:
            raise ImportError(
                "gTTS is required for TTS. Install with: pip install gtts"
            )
        if engine == 'edge-tts' and not EDGE_TTS_AVAILABLE:
            raise ImportError(
                "edge-tts is required for TTS. Install with: pip install edge-tts"
            )
        if engine == 'pyttsx3' and not PYTTSX3_AVAILABLE:
            raise ImportError(
                "pyttsx3 is required for TTS. Install with: pip install pyttsx3"
            )
    
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
            lang: Language override (uses self.lang if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
        
        lang = lang or self.lang
        
        try:
            if self.engine == 'gtts':
                return await self._generate_gtts(text, output_path, lang)
            elif self.engine == 'edge-tts':
                return await self._generate_edge_tts(text, output_path, lang)
            elif self.engine == 'pyttsx3':
                return await self._generate_pyttsx3(text, output_path)
            else:
                logger.warning(f"Unknown TTS engine: {self.engine}")
                return False
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}", exc_info=True)
            raise TTSGenerationError(f"Failed to generate TTS audio: {e}") from e
    
    async def _generate_gtts(self, text: str, output_path: Path, lang: str) -> bool:
        """Generate audio using gTTS (Google Text-to-Speech)."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._gtts_sync,
                text,
                output_path,
                lang
            )
            return output_path.exists()
        except Exception as e:
            logger.error(f"Error in gTTS generation: {e}", exc_info=True)
            raise TTSGenerationError(f"gTTS generation failed: {e}") from e
    
    def _gtts_sync(self, text: str, output_path: Path, lang: str):
        """Synchronous gTTS generation."""
        tts = gTTS(text=text, lang=lang, slow=self.slow)
        tts.save(str(output_path))
    
    async def _generate_edge_tts(self, text: str, output_path: Path, lang: str) -> bool:
        """Generate audio using edge-tts (Microsoft Edge TTS API)."""
        try:
            lang_map = {
                'pt-br': 'pt-BR',
                'pt': 'pt-BR',
                'en': 'en-US',
                'es': 'es-ES',
            }
            edge_lang = lang_map.get(lang.lower(), lang)
            
            # Use specified voice or find one for the language
            voices = await edge_tts.list_voices()
            selected_voice = None
            
            if self.voice:
                # Use specified voice
                for v in voices:
                    if v.get('ShortName') == self.voice or v.get('Name') == self.voice:
                        selected_voice = v.get('ShortName') or v.get('Name')
                        break
                if not selected_voice:
                    logger.warning(f"Voz especificada '{self.voice}' não encontrada, usando padrão")
            
            if not selected_voice:
                # Try to find a voice for the language (prefer female voices for pt-BR)
                for v in voices:
                    if edge_lang.lower() in v.get('Locale', '').lower():
                        # Prefer female voices for pt-BR (more natural)
                        if edge_lang == 'pt-BR' and v.get('Gender') == 'Female':
                            selected_voice = v.get('ShortName') or v.get('Name')
                            break
                        elif not selected_voice:
                            selected_voice = v.get('ShortName') or v.get('Name')
            
            # Fallback to first available voice if language not found
            if not selected_voice and voices:
                selected_voice = voices[0].get('ShortName') or voices[0].get('Name')
            
            if not selected_voice:
                logger.warning("Nenhuma voz disponível para edge-tts")
                return False
            
            logger.info(f"Usando voz edge-tts: {selected_voice}")
            
            # Build SSML if we have prosody parameters (rate, pitch, volume)
            if self.rate or self.pitch or self.volume:
                ssml_text = self._build_ssml(text, selected_voice, edge_lang)
                communicate = edge_tts.Communicate(ssml_text, selected_voice)
            else:
                # Generate audio without SSML (normal text)
                communicate = edge_tts.Communicate(text, selected_voice)
            
            await communicate.save(str(output_path))
            return output_path.exists()
        except Exception as e:
            logger.error(f"Error in edge-tts generation: {e}", exc_info=True)
            raise TTSGenerationError(f"edge-tts generation failed: {e}") from e
    
    def _build_ssml(self, text: str, voice: str, lang: str) -> str:
        """Build SSML (Speech Synthesis Markup Language) text for edge-tts."""
        prosody_attrs = []
        if self.rate:
            prosody_attrs.append(f'rate="{self.rate}"')
        if self.pitch:
            prosody_attrs.append(f'pitch="{self.pitch}"')
        if self.volume:
            prosody_attrs.append(f'volume="{self.volume}"')
        
        prosody_attr_str = ' '.join(prosody_attrs) if prosody_attrs else ''
        
        # Escape XML special characters
        text_escaped = (text
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;')
                       .replace('"', '&quot;')
                       .replace("'", '&apos;'))
        
        # Build SSML
        if prosody_attr_str:
            ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">
    <voice name="{voice}">
        <prosody {prosody_attr_str}>
            {text_escaped}
        </prosody>
    </voice>
</speak>'''
        else:
            ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">
    <voice name="{voice}">
        {text_escaped}
    </voice>
</speak>'''
        
        return ssml
    
    async def _generate_pyttsx3(self, text: str, output_path: Path) -> bool:
        """Generate audio using pyttsx3 (offline/local TTS)."""
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
    
    async def speak(self, text: str, lang: Optional[str] = None) -> Optional[Path]:
        """
        Generate audio and return path.
        
        Args:
            text: Text to speak
            lang: Language override
            
        Returns:
            Path to audio file or None if failed
        """
        if not text or not text.strip():
            return None
        
        from pathlib import Path
        import tempfile
        
        output_dir = Path(tempfile.gettempdir()) / "playwright_simple_audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_path = output_dir / f"tts_{text_hash}.mp3"
        
        success = await self.generate_audio(text, output_path, lang)
        if success:
            return output_path
        return None

