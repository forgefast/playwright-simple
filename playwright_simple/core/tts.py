#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-to-Speech (TTS) module for playwright-simple.

Provides automatic narration generation from test steps using various TTS engines.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
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
        test_name: str,
        return_timed_audio: bool = False
    ) -> Optional[Path]:
        """
        Generate narration audio from test steps.
        
        Args:
            test_steps: List of test steps (TestStep objects or dicts with 'text' or 'description')
            output_dir: Directory to save audio files
            test_name: Name of test (for filename)
            return_timed_audio: If True, concatenates audio with silence between steps based on start times
            
        Returns:
            Path to concatenated audio file (with silence if return_timed_audio=True), or None if generation failed
        """
        if not test_steps:
            return None
        
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / f"{test_name}_tts_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        audio_files = []
        timed_audio_list = []  # List of (audio_path, start_time_seconds, duration_seconds) tuples
        
        try:
            # Import TestStep here to avoid circular dependency
            from .step import TestStep
            
            # Generate audio for each step
            # Track current audio text for inheritance (similar to subtitles)
            # IMPORTANT: Include ALL steps to maintain video sync - steps without audio get silence
            current_audio_text = None
            for i, step in enumerate(test_steps, 1):
                # Handle both TestStep objects and dicts
                if isinstance(step, TestStep):
                    # Use audio field if available, otherwise fall back to subtitle/description
                    step_audio = getattr(step, 'audio', None)
                    if step_audio:
                        current_audio_text = step_audio
                    step_text = current_audio_text or step.subtitle or step.description or f'Passo {i}'
                    # Get start time from step (TestStep objects have start_time_seconds property)
                    step_start_time = getattr(step, 'start_time_seconds', None) or 0.0
                    step_duration = getattr(step, 'duration_seconds', None) or 0.0
                elif isinstance(step, dict):
                    # Check for audio field first, then inherit from previous if not specified
                    step_audio = step.get('audio') or step.get('speech')
                    if step_audio is not None:
                        # Explicit audio field: update current_audio_text
                        if step_audio == '':
                            # Empty string means clear audio
                            current_audio_text = None
                        else:
                            current_audio_text = step_audio
                    # If no audio field, current_audio_text continues from previous step
                    # Do NOT fall back to subtitle or description - audio must be explicitly set
                    # Only use current_audio_text if it exists (continuity)
                    step_text = current_audio_text if current_audio_text else None
                    # Get start time and duration from dict
                    step_start_time = step.get('start_time', 0.0)
                    step_duration = step.get('duration', 0.0)
                    # If duration not provided, try to calculate from end_time
                    if step_duration == 0.0 and 'end_time' in step:
                        step_duration = step.get('end_time', step_start_time) - step_start_time
                else:
                    # For other types, only use current_audio_text if it exists
                    step_text = current_audio_text if current_audio_text else None
                    step_start_time = 0.0
                    step_duration = 0.0
                
                # Generate audio or silence for this step
                if step_text and step_text.strip():
                    # Step has audio text - generate TTS
                    audio_file = temp_dir / f"step_{i}.mp3"
                    
                    logger.info(f"Generating narration for step {i} (starts at {step_start_time:.2f}s, duration {step_duration:.2f}s): {step_text[:50]}...")
                    try:
                        success = await self.generate_audio(step_text, audio_file)
                        
                        if success and audio_file.exists():
                            audio_duration = self._get_audio_duration(audio_file)
                            
                            if return_timed_audio:
                                # Store with timestamp and duration for synchronized playback
                                timed_audio_list.append((audio_file, step_start_time, audio_duration, step_duration))
                            else:
                                audio_files.append(audio_file)
                        else:
                            logger.warning(f"Failed to generate audio for step {i}")
                            # Create silence file for this step to maintain sync
                            if return_timed_audio:
                                silence_file = temp_dir / f"silence_{i}.mp3"
                                if self._create_silence_file(silence_file, step_duration):
                                    timed_audio_list.append((silence_file, step_start_time, step_duration, step_duration))
                    except TTSGenerationError as e:
                        logger.error(f"TTS generation error for step {i}: {e}")
                        # Create silence file for this step to maintain sync
                        if return_timed_audio:
                            silence_file = temp_dir / f"silence_{i}.mp3"
                            if self._create_silence_file(silence_file, step_duration):
                                timed_audio_list.append((silence_file, step_start_time, step_duration, step_duration))
                else:
                    # Step has no audio - create silence file to maintain video sync
                    if return_timed_audio and step_duration > 0:
                        silence_file = temp_dir / f"silence_{i}.mp3"
                        logger.debug(f"Creating silence for step {i} (duration {step_duration:.2f}s)")
                        if self._create_silence_file(silence_file, step_duration):
                            timed_audio_list.append((silence_file, step_start_time, step_duration, step_duration))
            
            # Final audio file path
            final_audio = output_dir / f"{test_name}_narration.mp3"
            
            if return_timed_audio:
                # Concatenate with silence between steps based on start times
                # timed_audio_list includes both audio and silence files
                if not timed_audio_list:
                    logger.warning("No audio or silence files were generated")
                    return None
                await self._concatenate_timed_audio(timed_audio_list, final_audio, temp_dir)
            else:
                # Legacy mode: concatenate all audio files (no silence)
                if not audio_files:
                    logger.warning("No audio files were generated")
                    return None
                await self._concatenate_audio(audio_files, final_audio)
            
            # Cleanup temp files
            for audio_file in audio_files:
                if audio_file.exists():
                    audio_file.unlink()
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except:
                    pass
            
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
    
    def _create_silence_file(self, output_path: Path, duration: float) -> bool:
        """
        Create a silence audio file of specified duration.
        
        Args:
            output_path: Path to save silence file
            duration: Duration in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if duration <= 0:
            return False
        
        try:
            import subprocess
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found, cannot create silence file")
            return False
        
        try:
            # Generate silence using anullsrc
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=mono:sample_rate=24000',
                '-t', str(duration),
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and output_path.exists():
                logger.debug(f"Created silence file: {output_path.name} ({duration:.2f}s)")
                return True
            else:
                logger.warning(f"Failed to create silence file: {result.stderr[:200]}")
                return False
        except Exception as e:
            logger.warning(f"Error creating silence file: {e}")
            return False
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds using ffprobe.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if unable to determine
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Could not get audio duration for {audio_path.name}: {e}")
        return 0.0
    
    async def _concatenate_timed_audio(
        self,
        timed_audio_list: List[Tuple[Path, float, float, float]],  # (audio_path, start_time, audio_duration, step_duration)
        output_path: Path,
        temp_dir: Path
    ) -> bool:
        """
        Concatenate audio files with silence to fill step durations and maintain video sync.
        
        Args:
            timed_audio_list: List of (audio_path, start_time_seconds, audio_duration_seconds, step_duration_seconds) tuples
            output_path: Path to save concatenated audio
            temp_dir: Temporary directory for silence files
            
        Returns:
            True if successful
        """
        if not timed_audio_list:
            return False
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"ffmpeg not found. Cannot concatenate audio files: {e}")
            raise TTSGenerationError("ffmpeg is required for audio concatenation but was not found") from e
        
        # Sort by start time
        sorted_audio = sorted(timed_audio_list, key=lambda x: x[1])
        
        # Build list of files to concatenate
        # Each entry is (audio_path, start_time, audio_duration, step_duration)
        # We need to:
        # 1. Add silence before first audio if needed
        # 2. For each audio, pad it with silence to match step_duration
        # 3. Add silence between steps if there's a gap
        concat_files = []
        silence_files = []
        
        previous_end_time = 0.0
        
        for i, (audio_path, start_time, audio_duration, step_duration) in enumerate(sorted_audio):
            # Calculate silence needed before this step
            silence_before = start_time - previous_end_time
            
            # Add silence before step if needed
            if silence_before > 0.01:  # At least 10ms
                silence_file = temp_dir / f"silence_before_{i}.mp3"
                if self._create_silence_file(silence_file, silence_before):
                    concat_files.append(silence_file)
                    silence_files.append(silence_file)
                    logger.debug(f"Created {silence_before:.2f}s silence before step {i+1}")
            
            # Add audio file
            concat_files.append(audio_path)
            
            # Calculate silence needed after audio to fill step duration
            # If audio_duration < step_duration, pad with silence
            silence_after = step_duration - audio_duration
            if silence_after > 0.01:  # At least 10ms
                silence_file = temp_dir / f"silence_after_{i}.mp3"
                if self._create_silence_file(silence_file, silence_after):
                    concat_files.append(silence_file)
                    silence_files.append(silence_file)
                    logger.debug(f"Created {silence_after:.2f}s silence after step {i+1} audio (to fill step duration)")
            
            # Update previous end time (end of step, not end of audio)
            previous_end_time = start_time + step_duration
        
        if not concat_files:
            logger.warning("No files to concatenate")
            return False
        
        # Create file list for ffmpeg concat
        file_list = temp_dir / "concat_list.txt"
        with open(file_list, 'w') as f:
            for file_path in concat_files:
                # Use absolute path for concat
                abs_path = file_path.resolve()
                f.write(f"file '{abs_path}'\n")
        
        # Concatenate all files
        concat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(file_list),
            '-c', 'copy',  # Copy codec (faster, no re-encode)
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(
            concat_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Cleanup silence files
        for silence_file in silence_files:
            if silence_file.exists():
                try:
                    silence_file.unlink()
                except:
                    pass
        
        # Cleanup file list
        if file_list.exists():
            try:
                file_list.unlink()
            except:
                pass
        
        if result.returncode == 0 and output_path.exists():
            logger.info(f"Concatenated {len(sorted_audio)} audio files with silence into {output_path.name}")
            return True
        else:
            error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
            logger.error(f"Failed to concatenate audio: {error_msg}")
            raise TTSGenerationError(f"Failed to concatenate timed audio: {error_msg}")
    
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

