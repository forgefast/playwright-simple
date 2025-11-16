#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Manager.

Main class for managing text-to-speech generation.
"""

import asyncio
import hashlib
import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ..exceptions import TTSGenerationError
from .engines.gtts_engine import GTTSEngine
from .engines.edge_tts_engine import EdgeTTSEngine
from .engines.pyttsx3_engine import Pyttsx3Engine
from .audio_processing import concatenate_audio, concatenate_timed_audio
from .pre_generation import pre_generate_audios
from .utils import get_audio_duration, create_silence_file, play_audio_file

logger = logging.getLogger(__name__)


class TTSManager:
    """Manages text-to-speech generation for test narration."""
    
    def __init__(
        self,
        lang: str = 'pt-br',
        engine: str = 'gtts',
        slow: bool = False,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None
    ):
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
        self.engine_name = engine
        self.slow = slow
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        
        # Initialize engine
        if engine == 'gtts':
            self.engine = GTTSEngine(lang=lang, slow=slow, voice=voice, rate=rate, pitch=pitch, volume=volume)
            if not self.engine.is_available():
                raise ImportError("gTTS is required for TTS. Install with: pip install gtts")
        elif engine == 'edge-tts':
            self.engine = EdgeTTSEngine(lang=lang, slow=slow, voice=voice, rate=rate, pitch=pitch, volume=volume)
            if not self.engine.is_available():
                raise ImportError("edge-tts is required for TTS. Install with: pip install edge-tts")
        elif engine == 'pyttsx3':
            self.engine = Pyttsx3Engine(lang=lang, slow=slow, voice=voice, rate=rate, pitch=pitch, volume=volume)
            if not self.engine.is_available():
                raise ImportError("pyttsx3 is required for TTS. Install with: pip install pyttsx3")
        else:
            raise ValueError(f"Unknown TTS engine: {engine}")
    
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
            return await self.engine.generate(text, output_path, lang)
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}", exc_info=True)
            raise TTSGenerationError(f"Failed to generate TTS audio: {e}") from e
    
    async def pre_generate_audios(
        self,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        output_dir: Path,
        test_name: str
    ) -> Dict[str, Any]:
        """
        Pre-generate all audio files in parallel and calculate adjusted timestamps.
        
        This method generates all audios BEFORE step execution, allowing the StepExecutor
        to wait for previous audio to finish before executing the next step with audio.
        
        Args:
            test_steps: List of test steps (TestStep objects or dicts)
            output_dir: Directory to save audio files
            test_name: Name of test (for filename)
            
        Returns:
            Dictionary with:
                - 'audio_data': Dict mapping step_index -> (audio_file, audio_duration)
                - 'adjusted_timestamps': Dict mapping step_index -> adjusted_start_time
                - 'audio_end_times': Dict mapping step_index -> when audio ends
        """
        return await pre_generate_audios(
            test_steps,
            output_dir,
            test_name,
            self.generate_audio
        )
    
    async def generate_narration(
        self,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        output_dir: Path,
        test_name: str,
        return_timed_audio: bool = False
    ) -> Optional[Path]:
        """
        Generate narration audio from test steps.
        
        This method uses pre-generated audio files (if available) or generates them on-demand.
        Steps should already have audio_file_path and audio_duration_seconds set if pre-generated.
        
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
        timed_audio_list = []  # List of (audio_path, start_time_seconds, audio_duration, step_duration, has_audio) tuples
        
        try:
            # Import TestStep here to avoid circular dependency
            try:
                from ..step import TestStep
            except ImportError:
                TestStep = None
            
            # First pass: Check if steps already have pre-generated audio
            # If so, use those directly. Otherwise, generate on-demand.
            steps_have_pre_generated_audio = False
            if TestStep is not None:
                steps_with_audio = [s for s in test_steps if isinstance(s, TestStep) and 
                                   hasattr(s, 'audio_file_path') and s.audio_file_path and
                                   hasattr(s, 'audio_duration_seconds') and s.audio_duration_seconds]
                if steps_with_audio:
                    steps_have_pre_generated_audio = True
                    logger.info(f"🎵 Using {len(steps_with_audio)} pre-generated audio files from steps")
            
            if steps_have_pre_generated_audio and return_timed_audio:
                # Steps already have pre-generated audio - use it directly
                # Video was already recorded with correct timestamps (waits included)
                # Group consecutive steps with same audio_file_path to avoid duplication
                current_group = None
                for step in test_steps:
                    if isinstance(step, TestStep) and step.audio_file_path and step.audio_duration_seconds:
                        step_start = step.start_time_seconds
                        step_duration = step.duration_seconds or 0.0
                        if step_duration == 0.0:
                            step_duration = (step.end_time_seconds - step_start) if step.end_time_seconds else 0.0
                        
                        if current_group and current_group['audio_path'] == step.audio_file_path:
                            # Same audio file - extend group duration
                            current_group['step_duration'] += step_duration
                            current_group['end_time'] = step_start + step_duration
                        else:
                            # New audio file - save previous group and start new
                            if current_group:
                                timed_audio_list.append((
                                    current_group['audio_path'],
                                    current_group['start_time'],
                                    current_group['audio_duration'],
                                    current_group['step_duration'],
                                    True
                                ))
                            current_group = {
                                'audio_path': step.audio_file_path,
                                'audio_duration': step.audio_duration_seconds,
                                'start_time': step_start,
                                'step_duration': step_duration,
                                'end_time': step_start + step_duration
                            }
                    elif isinstance(step, TestStep):
                        # Step without audio - save current group if exists
                        if current_group:
                            timed_audio_list.append((
                                current_group['audio_path'],
                                current_group['start_time'],
                                current_group['audio_duration'],
                                current_group['step_duration'],
                                True
                            ))
                            current_group = None
                        
                        # Add silence for step without audio
                        step_start = step.start_time_seconds
                        step_duration = step.duration_seconds or 0.0
                        if step_duration == 0.0:
                            step_duration = (step.end_time_seconds - step_start) if step.end_time_seconds else 0.0
                        
                        if step_duration > 0:
                            silence_file = temp_dir / f"silence_step_{step.step_number}.mp3"
                            if create_silence_file(silence_file, step_duration):
                                timed_audio_list.append((
                                    silence_file,
                                    step_start,
                                    step_duration,
                                    step_duration,
                                    False
                                ))
                
                # Don't forget the last group
                if current_group:
                    timed_audio_list.append((
                        current_group['audio_path'],
                        current_group['start_time'],
                        current_group['audio_duration'],
                        current_group['step_duration'],
                        True
                    ))
            else:
                # Generate audio on-demand (fallback for compatibility)
                # Track current audio text for inheritance (similar to subtitles)
                prepared_steps = []
                current_audio_text = None
                for i, step in enumerate(test_steps, 1):
                    # Handle both TestStep objects and dicts
                    if isinstance(step, TestStep):
                        step_audio = getattr(step, 'audio', None)
                        if step_audio is not None:
                            if step_audio == '':
                                current_audio_text = None
                            else:
                                current_audio_text = step_audio
                        step_text = current_audio_text if current_audio_text else None
                        step_start_time = step.start_time_seconds
                        step_duration = step.duration_seconds or 0.0
                        if step_duration == 0.0:
                            step_duration = step.end_time_seconds - step_start_time
                    elif isinstance(step, dict):
                        step_audio = step.get('audio') or step.get('speech')
                        if step_audio is not None:
                            if step_audio == '':
                                current_audio_text = None
                            else:
                                current_audio_text = step_audio
                        step_text = current_audio_text if current_audio_text else None
                        step_start_time = step.get('start_time', 0.0)
                        step_duration = step.get('duration', 0.0)
                        if step_duration == 0.0 and 'end_time' in step:
                            step_duration = step.get('end_time', step_start_time) - step_start_time
                    else:
                        step_text = current_audio_text if current_audio_text else None
                        step_start_time = 0.0
                        step_duration = 0.0
                    
                    prepared_steps.append({
                        'audio_text': step_text,
                        'start_time': step_start_time,
                        'duration': step_duration,
                        'step_index': i,
                        'original_step': step
                    })
                
                # Group consecutive steps with same audio text
                audio_groups = []
                current_group = None
                
                for step_data in prepared_steps:
                    audio_text = step_data['audio_text']
                    start_time = step_data['start_time']
                    duration = step_data['duration']
                    
                    if audio_text and audio_text.strip():
                        if current_group and current_group['audio_text'] == audio_text:
                            current_group['duration'] += duration
                            current_group['end_time'] = start_time + duration
                        else:
                            if current_group:
                                audio_groups.append(current_group)
                            current_group = {
                                'audio_text': audio_text,
                                'start_time': start_time,
                                'duration': duration,
                                'end_time': start_time + duration
                            }
                    else:
                        if current_group:
                            audio_groups.append(current_group)
                            current_group = None
                        if return_timed_audio and duration > 0:
                            audio_groups.append({
                                'audio_text': None,
                                'start_time': start_time,
                                'duration': duration,
                                'end_time': start_time + duration
                            })
                
                if current_group:
                    audio_groups.append(current_group)
                
                # Generate audio files in parallel
                logger.info(f"🎵 Generating {len([g for g in audio_groups if g.get('audio_text')])} audio files in parallel...")
                
                async def generate_group_audio(group_idx: int, group: Dict[str, Any]) -> Tuple[int, Optional[Path], Optional[float], bool]:
                    """Generate audio for a single group"""
                    if group['audio_text'] and group['audio_text'].strip():
                        audio_file = temp_dir / f"group_{group_idx}.mp3"
                        try:
                            success = await self.generate_audio(group['audio_text'], audio_file)
                            if success and audio_file.exists():
                                audio_duration = get_audio_duration(audio_file)
                                return (group_idx, audio_file, audio_duration, True)
                            else:
                                return (group_idx, None, None, False)
                        except Exception as e:
                            logger.error(f"TTS generation error for group {group_idx}: {e}")
                            return (group_idx, None, None, False)
                    else:
                        return (group_idx, None, None, False)
                
                audio_generation_tasks = []
                for group_idx, group in enumerate(audio_groups, 1):
                    if group.get('audio_text') and group['audio_text'].strip():
                        audio_generation_tasks.append(generate_group_audio(group_idx, group))
                
                audio_results = await asyncio.gather(*audio_generation_tasks, return_exceptions=True)
                
                audio_results_dict = {}
                for result in audio_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error generating audio: {result}")
                        continue
                    group_idx, audio_file, audio_duration, success = result
                    if success and audio_file:
                        audio_results_dict[group_idx] = (audio_file, audio_duration)
                
                # Process groups and build timed_audio_list
                for group_idx, group in enumerate(audio_groups, 1):
                    if group['audio_text'] and group['audio_text'].strip():
                        if group_idx in audio_results_dict:
                            audio_file, audio_duration = audio_results_dict[group_idx]
                            
                            # Store audio data in steps
                            for prep_step in prepared_steps:
                                if (prep_step['start_time'] >= group['start_time'] and 
                                    prep_step['start_time'] < group.get('end_time', group['start_time'] + group['duration']) and
                                    prep_step['audio_text'] == group['audio_text']):
                                    original_step = prep_step.get('original_step')
                                    if isinstance(original_step, TestStep):
                                        original_step.audio_file_path = audio_file
                                        original_step.audio_duration_seconds = audio_duration
                            
                            if return_timed_audio:
                                timed_audio_list.append((audio_file, group['start_time'], audio_duration, group['duration'], True))
                            else:
                                audio_files.append(audio_file)
                        else:
                            logger.warning(f"Failed to generate audio for group {group_idx}")
                            if return_timed_audio:
                                silence_file = temp_dir / f"silence_group_{group_idx}.mp3"
                                if create_silence_file(silence_file, group['duration']):
                                    timed_audio_list.append((silence_file, group['start_time'], group['duration'], group['duration'], False))
                    else:
                        if return_timed_audio and group['duration'] > 0:
                            silence_file = temp_dir / f"silence_group_{group_idx}.mp3"
                            logger.debug(f"Creating silence for group {group_idx} (duration {group['duration']:.2f}s)")
                            if create_silence_file(silence_file, group['duration']):
                                timed_audio_list.append((silence_file, group['start_time'], group['duration'], group['duration'], False))
            
            # Final audio file path
            final_audio = output_dir / f"{test_name}_narration.mp3"
            
            if return_timed_audio:
                # Concatenate with silence between steps based on start times
                # timed_audio_list includes both audio and silence files
                if not timed_audio_list:
                    logger.warning("No audio or silence files were generated")
                    return None
                await concatenate_timed_audio(timed_audio_list, final_audio, temp_dir)
            else:
                # Legacy mode: concatenate all audio files (no silence)
                if not audio_files:
                    logger.warning("No audio files were generated")
                    return None
                await concatenate_audio(audio_files, final_audio)
            
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
    
    async def play_audio_realtime(self, text: str, cache_dir: Optional[Path] = None) -> float:
        """
        Generate and play audio in real-time, returning the actual duration.
        
        This method generates audio, plays it, and waits for playback to complete.
        Used for synchronizing step execution with audio playback.
        
        Args:
            text: Text to convert to speech and play
            cache_dir: Optional directory to cache generated audio files
            
        Returns:
            Actual audio duration in seconds
        """
        if not text or not text.strip():
            return 0.0
        
        # Use cache if available
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Create hash-based filename for caching
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            audio_file = cache_dir / f"{text_hash}.mp3"
            
            # Check if cached
            if audio_file.exists():
                logger.debug(f"Using cached audio for text: {text[:50]}...")
                duration = get_audio_duration(audio_file)
                await play_audio_file(audio_file)
                return duration
        
        # Generate audio to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            audio_file = Path(tmp_file.name)
        
        try:
            # Generate audio
            success = await self.generate_audio(text, audio_file)
            
            if not success or not audio_file.exists():
                logger.warning(f"Failed to generate audio for real-time playback: {text[:50]}...")
                return 0.0
            
            # Get actual duration
            duration = get_audio_duration(audio_file)
            
            # Save to cache if cache_dir provided
            if cache_dir and duration > 0:
                cache_dir.mkdir(parents=True, exist_ok=True)
                text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                cached_file = cache_dir / f"{text_hash}.mp3"
                if not cached_file.exists():
                    shutil.copy2(audio_file, cached_file)
                    logger.debug(f"Cached audio file: {cached_file.name}")
            
            # Play audio and wait for completion
            await play_audio_file(audio_file)
            
            return duration
            
        finally:
            # Cleanup temporary file
            if audio_file.exists():
                try:
                    audio_file.unlink()
                except:
                    pass
    
    # Expose utility methods for backward compatibility
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration (backward compatibility)."""
        return get_audio_duration(audio_path)
    
    def _create_silence_file(self, output_path: Path, duration: float) -> bool:
        """Create silence file (backward compatibility)."""
        return create_silence_file(output_path, duration)
    
    async def _play_audio_file(self, audio_file: Path) -> None:
        """Play audio file (backward compatibility)."""
        return await play_audio_file(audio_file)

