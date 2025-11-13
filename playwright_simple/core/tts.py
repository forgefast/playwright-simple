#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-to-Speech (TTS) module for playwright-simple.

Provides automatic narration generation from test steps using various TTS engines.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
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
    
    def __init__(self, lang: str = 'pt-br', engine: str = 'gtts', slow: bool = False):
        """
        Initialize TTS manager.
        
        Args:
            lang: Language code (pt-br, en, es, etc.)
            engine: TTS engine to use ('gtts', 'edge-tts', or 'pyttsx3')
            slow: Whether to speak slowly (gTTS only, ignored for other engines)
        """
        self.lang = lang
        self.engine = engine
        self.slow = slow
        
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
            # Run in thread pool to avoid blocking
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
        """
        Generate audio using edge-tts (Microsoft Edge TTS API).
        
        More performatic and lightweight than gTTS, uses Edge browser's TTS API.
        Free to use, no strict rate limits.
        """
        try:
            # Map language codes to edge-tts format
            lang_map = {
                'pt-br': 'pt-BR',
                'pt': 'pt-BR',
                'en': 'en-US',
                'es': 'es-ES',
            }
            edge_lang = lang_map.get(lang.lower(), lang)
            
            # Get available voices for the language
            voices = await edge_tts.list_voices()
            voice = None
            
            # Try to find a voice for the language
            for v in voices:
                if edge_lang.lower() in v['Locale'].lower():
                    voice = v['Name']
                    break
            
            # Fallback to first available voice if language not found
            if not voice and voices:
                voice = voices[0]['Name']
            
            if not voice:
                print(f"  ⚠️  Nenhuma voz disponível para edge-tts")
                return False
            
            # Generate audio
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            
            return output_path.exists()
        except Exception as e:
            logger.error(f"Error in edge-tts generation: {e}", exc_info=True)
            raise TTSGenerationError(f"edge-tts generation failed: {e}") from e
    
    async def _generate_pyttsx3(self, text: str, output_path: Path) -> bool:
        """Generate audio using pyttsx3 (offline, but lower quality)."""
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
    
    async def generate_narration(
        self,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        output_dir: Path,
        test_name: str
    ) -> Optional[Path]:
        """
        Generate narration audio from test steps.
        
        Args:
            test_steps: List of test steps (TestStep objects or dicts with 'text' or 'description')
            output_dir: Directory to save audio files
            test_name: Name of test (for filename)
            
        Returns:
            Path to concatenated audio file, or None if generation failed
        """
        if not test_steps:
            return None
        
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / f"{test_name}_tts_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        audio_files = []
        
        try:
            # Import TestStep here to avoid circular dependency
            from .step import TestStep
            
            # Generate audio for each step
            for i, step in enumerate(test_steps, 1):
                # Handle both TestStep objects and dicts
                if isinstance(step, TestStep):
                    step_text = step.subtitle or step.description or f'Passo {i}'
                elif isinstance(step, dict):
                    step_text = step.get('text') or step.get('description') or f'Passo {i}'
                else:
                    step_text = f'Passo {i}'
                
                if not step_text or not step_text.strip():
                    continue
                
                audio_file = temp_dir / f"step_{i}.mp3"
                
                logger.info(f"Generating narration for step {i}: {step_text[:50]}...")
                try:
                    success = await self.generate_audio(step_text, audio_file)
                    
                    if success and audio_file.exists():
                        audio_files.append(audio_file)
                    else:
                        logger.warning(f"Failed to generate audio for step {i}")
                except TTSGenerationError as e:
                    logger.error(f"TTS generation error for step {i}: {e}")
                    continue
            
            if not audio_files:
                logger.warning("No audio files were generated")
                return None
            
            # Concatenate all audio files
            final_audio = output_dir / f"{test_name}_narration.mp3"
            await self._concatenate_audio(audio_files, final_audio)
            
            # Cleanup temp files
            for audio_file in audio_files:
                if audio_file.exists():
                    audio_file.unlink()
            temp_dir.rmdir()
            
            if final_audio.exists():
                logger.info(f"Narration generated: {final_audio.name}")
                return final_audio
            else:
                return None
                
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating narration: {e}", exc_info=True)
            raise TTSGenerationError(f"Failed to generate narration: {e}") from e
            # Cleanup on error
            for audio_file in audio_files:
                if audio_file.exists():
                    audio_file.unlink()
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except:
                    pass
            return None
    
    async def _concatenate_audio(
        self,
        audio_files: List[Path],
        output_path: Path
    ) -> bool:
        """
        Concatenate multiple audio files into one.
        
        Args:
            audio_files: List of audio file paths
            output_path: Path to save concatenated audio
            
        Returns:
            True if successful
        """
        if not audio_files:
            return False
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"ffmpeg not found. Cannot concatenate audio files: {e}")
            raise TTSGenerationError("ffmpeg is required for audio concatenation but was not found") from e
        
        # Create file list for ffmpeg concat
        file_list = output_path.parent / "concat_list.txt"
        with open(file_list, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.absolute()}'\n")
        
        try:
            # Concatenate using ffmpeg
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(file_list),
                '-c', 'copy',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Cleanup
            if file_list.exists():
                file_list.unlink()
            
            if result.returncode == 0 and output_path.exists():
                return True
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                logger.error(f"Error concatenating audio: {error_msg}")
                raise TTSGenerationError(f"Failed to concatenate audio files: {error_msg}")
                
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error concatenating audio: {e}", exc_info=True)
            if file_list.exists():
                file_list.unlink()
            raise TTSGenerationError(f"Failed to concatenate audio files: {e}") from e

