#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playback module.

Provides functionality for executing YAML steps in read mode.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .step_executor import StepExecutor
from .page_stability import wait_for_page_stable
from ..tts import TTSManager

logger = logging.getLogger(__name__)


def estimate_audio_duration(text: str) -> float:
    """
    Estimate audio duration based on text length.
    
    Uses average speaking rate for Portuguese: ~150 words/min = 2.5 words/sec
    For Portuguese, average word length is ~5 characters, so ~12.5 chars/sec
    We use a conservative estimate of ~10 chars/sec to account for pauses.
    
    Args:
        text: Text to estimate duration for
        
    Returns:
        Estimated duration in seconds
    """
    if not text or not text.strip():
        return 0.0
    
    # Average speaking rate: ~10 characters per second for Portuguese
    # Add 0.5s buffer for natural pauses
    char_count = len(text.strip())
    estimated_seconds = (char_count / 10.0) + 0.5
    
    # Minimum duration: 0.5s
    return max(0.5, estimated_seconds)


async def play_audio_for_step(tts_manager: Optional[TTSManager], text: str, cache_dir: Optional[Path] = None, estimate_audio_duration_func=None) -> float:
    """
    Play audio for a step in real-time.
    
    Args:
        tts_manager: TTSManager instance (or None if not available)
        text: Text to convert to speech and play
        cache_dir: Optional directory to cache generated audio files
        
    Returns:
        Actual audio duration in seconds, or 0.0 if playback failed
    """
    if not text or not text.strip():
        return 0.0
    
    estimate_func = estimate_audio_duration_func or estimate_audio_duration
    
    if not tts_manager:
        # Fallback to estimated duration
        return estimate_func(text)
    
    try:
        duration = await tts_manager.play_audio_realtime(text, cache_dir)
        logger.debug(f"🎤 Played audio for step: '{text[:50]}...' (duration: {duration:.2f}s)")
        return duration
    except Exception as e:
        logger.warning(f"Failed to play audio for step: {e}")
        # Fallback to estimated duration
        return estimate_func(text)


def get_tts_manager(video_config, video_dir: Optional[Path] = None):
    """
    Get or create TTSManager for real-time audio playback.
    
    Args:
        video_config: VideoConfig object with audio settings
        video_dir: Optional video directory for cache
        
    Returns:
        Tuple of (TTSManager instance or None, cache_dir or None)
    """
    # Check if audio is enabled in video config
    if not (video_config and (video_config.audio or video_config.narration)):
        logger.debug("Audio not enabled in video config")
        return None, None
    
    try:
        # Determine which config to use
        use_audio_config = video_config.audio if hasattr(video_config, 'audio') else False
        if use_audio_config:
            lang = video_config.audio_lang
            engine = video_config.audio_engine
            voice = getattr(video_config, 'audio_voice', None)
            rate = getattr(video_config, 'audio_rate', None)
            pitch = getattr(video_config, 'audio_pitch', None)
            volume = getattr(video_config, 'audio_volume', None)
        else:
            lang = video_config.narration_lang
            engine = video_config.narration_engine
            voice = getattr(video_config, 'narration_voice', None)
            rate = None
            pitch = None
            volume = None
        
        # Default to edge-tts if not specified
        if not engine or engine == 'gtts':
            engine = 'edge-tts'
        
        tts_manager = TTSManager(
            lang=lang,
            engine=engine,
            slow=False,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        # Create cache directory for audio files
        cache_dir = None
        if video_dir:
            cache_dir = Path(video_dir) / 'audio_cache'
        return tts_manager, cache_dir
    except Exception as e:
        logger.warning(f"Failed to create TTSManager for real-time playback: {e}")
        return None, None


async def execute_yaml_steps(
    yaml_steps: List[Dict[str, Any]],
    page,
    command_handlers,
    recorder_logger,
    speed_level,
    video_start_time: datetime,
    video_config = None,
    video_dir: Optional[Path] = None
) -> List[Any]:
    """
    Execute YAML steps using StepExecutor.
    
    Args:
        yaml_steps: List of step dictionaries from YAML
        page: Playwright Page instance
        command_handlers: CommandHandlers instance
        recorder_logger: RecorderLogger instance
        speed_level: SpeedLevel enum
        video_start_time: Video recording start time
        video_config: Optional VideoConfig for audio
        video_dir: Optional video directory for audio cache
        
    Returns:
        List of TestStep objects with all timing and content data
    """
    from .step_executor import StepExecutor
    
    if not yaml_steps:
        logger.warning("No YAML steps to execute")
        return []
    
    if not page:
        error_msg = "No page available for executing steps!"
        if recorder_logger:
            recorder_logger.log_critical_failure(
                action='execute_yaml_steps',
                error=error_msg,
                page_state=None,
                details={}
            )
        logger.error(error_msg)
        raise RuntimeError("Page not available")
    
    # Get video start time
    if not video_start_time:
        video_start_time = datetime.now()
    
    # PRE-GENERATE ALL AUDIOS BEFORE EXECUTING STEPS
    # This allows StepExecutor to wait for previous audio to finish
    pre_generated_audio_info = None
    if video_config and (video_config.audio or video_config.narration):
        try:
            # Determine which config to use
            use_audio_config = video_config.audio if hasattr(video_config, 'audio') else False
            if use_audio_config:
                lang = video_config.audio_lang
                engine = video_config.audio_engine
                voice = getattr(video_config, 'audio_voice', None)
                rate = getattr(video_config, 'audio_rate', None)
                pitch = getattr(video_config, 'audio_pitch', None)
                volume = getattr(video_config, 'audio_volume', None)
            else:
                lang = video_config.narration_lang
                engine = video_config.narration_engine
                voice = getattr(video_config, 'narration_voice', None)
                rate = None
                pitch = None
                volume = None
            
            if not engine or engine == 'gtts':
                engine = 'edge-tts'
            
            # Create TTSManager for pre-generation
            tts_manager = TTSManager(
                lang=lang,
                engine=engine,
                slow=False,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            
            # Pre-generate all audios in parallel
            logger.info("🎵 Pre-generating all audios before step execution...")
            # Extract test name from YAML or use default
            test_name = 'test'  # Will be passed from caller
            if not video_dir:
                video_dir = Path('videos')
            
            pre_generated_audio_info = await tts_manager.pre_generate_audios(
                yaml_steps,
                video_dir,
                test_name
            )
            
            logger.info(f"🎵 Pre-generated {len(pre_generated_audio_info.get('audio_data', {}))} audio files")
            
        except Exception as e:
            logger.warning(f"Failed to pre-generate audios: {e}. Will proceed without audio sync.")
            logger.debug(f"Pre-generation error details: {e}", exc_info=True)
            pre_generated_audio_info = None
    
    # Get TTS manager for real-time playback (if needed)
    tts_manager, audio_cache_dir = get_tts_manager(video_config, video_dir) if video_config else (None, None)
    
    # Create wait_for_page_stable function
    async def wait_for_page_stable_func(timeout: float = 10.0):
        await wait_for_page_stable(
            page,
            timeout=timeout,
            speed_level=speed_level,
            fast_mode=False,  # Use speed_level instead
            recorder_logger=recorder_logger
        )
    
    # Create play_audio_for_step function
    async def play_audio_for_step_func(text: str) -> float:
        return await play_audio_for_step(tts_manager, text, audio_cache_dir)
    
    # Initialize step executor with pre-generated audio info
    executor = StepExecutor(
        page=page,
        command_handlers=command_handlers,
        recorder_logger=recorder_logger,
        speed_level=speed_level,
        video_start_time=video_start_time,
        wait_for_page_stable=wait_for_page_stable_func,
        play_audio_for_step=play_audio_for_step_func,
        estimate_audio_duration=estimate_audio_duration,
        pre_generated_audio_info=pre_generated_audio_info
    )
    
    # Execute steps - now returns list of TestStep objects
    steps = await executor.execute_steps(yaml_steps)
    
    # Debug: show what's in steps (only in debug mode)
    if recorder_logger and recorder_logger.is_debug and steps:
        from ...step import TestStep
        steps_with_subtitle = sum(1 for s in steps if isinstance(s, TestStep) and s.subtitle)
        steps_with_audio = sum(1 for s in steps if isinstance(s, TestStep) and s.audio)
        logger.info(f"🎬 DEBUG: Steps with subtitle: {steps_with_subtitle}/{len(steps)}")
        logger.info(f"🎬 DEBUG: Steps with audio: {steps_with_audio}/{len(steps)}")
    
    logger.info("✅ All YAML steps executed successfully")
    
    # Wait a bit after all steps to ensure video captures everything
    await asyncio.sleep(0.5)
    
    return steps

