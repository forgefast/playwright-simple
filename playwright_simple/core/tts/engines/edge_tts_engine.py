#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS Engine implementation.

Microsoft Edge TTS API engine for TTS generation.
"""

import logging
from pathlib import Path
from typing import Optional

from .base import BaseTTSEngine
from ...exceptions import TTSGenerationError

logger = logging.getLogger(__name__)

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    edge_tts = None


class EdgeTTSEngine(BaseTTSEngine):
    """edge-tts (Microsoft Edge TTS API) engine implementation."""
    
    def is_available(self) -> bool:
        """Check if edge-tts is available."""
        return EDGE_TTS_AVAILABLE
    
    async def generate(self, text: str, output_path: Path, lang: Optional[str] = None) -> bool:
        """
        Generate audio using edge-tts (Microsoft Edge TTS API).
        
        More performatic and lightweight than gTTS, uses Edge browser's TTS API.
        Free to use, no strict rate limits.
        """
        if not self.is_available():
            raise ImportError(
                "edge-tts is required for TTS. Install with: pip install edge-tts"
            )
        
        try:
            # Map language codes to edge-tts format
            lang_map = {
                'pt-br': 'pt-BR',
                'pt': 'pt-BR',
                'en': 'en-US',
                'es': 'es-ES',
            }
            edge_lang = lang_map.get((lang or self.lang).lower(), lang or self.lang)
            
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
                print(f"  ⚠️  Nenhuma voz disponível para edge-tts")
                return False
            
            logger.info(f"Usando voz edge-tts: {selected_voice}")
            
            # Build SSML if we have prosody parameters (rate, pitch, volume)
            if self.rate or self.pitch or self.volume:
                ssml_text = self._build_ssml(text, selected_voice, edge_lang)
                # Use SSML for generation
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
        """
        Build SSML (Speech Synthesis Markup Language) text for edge-tts.
        
        Allows control over rate (speed), pitch (tone), and volume.
        """
        # Build prosody attributes
        prosody_attrs = []
        if self.rate:
            prosody_attrs.append(f'rate="{self.rate}"')
        if self.pitch:
            prosody_attrs.append(f'pitch="{self.pitch}"')
        if self.volume:
            prosody_attrs.append(f'volume="{self.volume}"')
        
        prosody_attr_str = ' '.join(prosody_attrs) if prosody_attrs else ''
        
        # Escape XML special characters in text
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
            # No prosody, just voice
            ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">
    <voice name="{voice}">
        {text_escaped}
    </voice>
</speak>'''
        
        return ssml

