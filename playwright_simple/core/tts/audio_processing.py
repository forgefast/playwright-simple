#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Processing module.

Provides functions for concatenating and processing audio files.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

from ..exceptions import TTSGenerationError
from .utils import create_silence_file

logger = logging.getLogger(__name__)


async def concatenate_audio(
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
        
    Raises:
        TTSGenerationError: If concatenation fails
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


async def concatenate_timed_audio(
    timed_audio_list: List[Tuple[Path, float, float, float, bool]],  # (audio_path, start_time, audio_duration, step_duration, has_audio)
    output_path: Path,
    temp_dir: Path
) -> bool:
    """
    Concatenate audio files with silence to fill step durations and maintain video sync.
    
    IMPORTANT: If audio is longer than step duration, next step with audio must wait for audio to finish.
    Steps without audio can start before previous audio finishes.
    
    Args:
        timed_audio_list: List of (audio_path, start_time_seconds, audio_duration_seconds, step_duration_seconds, has_audio) tuples
        output_path: Path to save concatenated audio
        temp_dir: Temporary directory for silence files
        
    Returns:
        True if successful
        
    Raises:
        TTSGenerationError: If concatenation fails
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
    
    # First pass: Store audio list with original video timestamps
    adjusted_audio_list = []
    
    logger.info("🎵 AUDIO SYNC: Starting timestamp calculation pass")
    logger.info(f"🎵 AUDIO SYNC: Total audio groups: {len(sorted_audio)}")
    
    for i, (audio_path, start_time, audio_duration, step_duration, has_audio) in enumerate(sorted_audio):
        # Calculate when this audio actually ends
        audio_end_time = start_time + audio_duration
        step_end_time = start_time + step_duration
        
        logger.info(f"🎵 AUDIO SYNC: Step {i+1} - video start: {start_time:.2f}s, audio: {audio_duration:.2f}s, step: {step_duration:.2f}s")
        logger.info(f"🎵 AUDIO SYNC: Step {i+1} - audio ends: {audio_end_time:.2f}s, step ends: {step_end_time:.2f}s")
        
        if has_audio:
            if audio_duration > step_duration:
                logger.info(f"🎵 AUDIO SYNC: Step {i+1} audio extends {audio_duration - step_duration:.2f}s beyond step end")
        else:
            logger.info(f"🎵 AUDIO SYNC: Step {i+1} has no audio")
        
        # Store entry (start_time is when step starts in video)
        adjusted_audio_list.append((audio_path, start_time, audio_duration, step_duration, has_audio))
    
    # Second pass: Calculate adjusted audio start times
    # Audio should start when step starts in video, but if previous audio is still playing,
    # next audio should start immediately after previous audio ends
    logger.info("🎵 AUDIO SYNC: Calculating adjusted audio start times")
    adjusted_audio_start_times = []  # When each audio actually should start in concatenated timeline
    last_audio_end = 0.0  # Track when the last audio actually ended
    
    for i, (audio_path, video_start_time, audio_duration, step_duration, has_audio) in enumerate(adjusted_audio_list):
        if has_audio:
            # Audio should start when step starts in video to maintain sync with video
            # But if previous audio is still playing, start immediately after it ends
            actual_start = max(video_start_time, last_audio_end)
            
            if actual_start > video_start_time:
                logger.debug(f"🎵 AUDIO SYNC: Step {i+1} - previous audio extends to {last_audio_end:.2f}s, audio will start at {actual_start:.2f}s (video step starts at {video_start_time:.2f}s)")
            
            adjusted_audio_start_times.append(actual_start)
            last_audio_end = actual_start + audio_duration
        else:
            # Step without audio - use video timestamp
            adjusted_audio_start_times.append(video_start_time)
            # Don't update last_audio_end - it remains as the end of the last audio
    
    # Third pass: Build concatenation list
    # Concatenate audio files sequentially using adjusted start times
    logger.info("🎵 AUDIO SYNC: Starting concatenation pass")
    concat_files = []
    silence_files = []
    current_time = 0.0
    
    for i, (audio_path, video_start_time, audio_duration, step_duration, has_audio) in enumerate(adjusted_audio_list):
        actual_audio_start = adjusted_audio_start_times[i]
        
        logger.info(f"🎵 AUDIO SYNC: Step {i+1} - video: {video_start_time:.2f}s, audio start: {actual_audio_start:.2f}s, duration: {audio_duration:.2f}s")
        
        # Add silence to reach actual_audio_start (only if we're behind)
        silence_before = actual_audio_start - current_time
        if silence_before > 0.01:
            # We need to add silence to reach the audio start time
            silence_file = temp_dir / f"silence_before_{i}.mp3"
            if create_silence_file(silence_file, silence_before):
                concat_files.append(silence_file)
                silence_files.append(silence_file)
                logger.info(f"🎵 AUDIO SYNC: Created {silence_before:.2f}s silence before step {i+1} (from {current_time:.2f}s to {actual_audio_start:.2f}s)")
                current_time += silence_before
        elif silence_before < -0.01:
            # We're already at or past the audio start time
            # This can happen if previous audio extended beyond this step's video start
            # For steps with audio, we've already adjusted the start time, so this shouldn't happen
            # For steps without audio, we just continue from current_time
            if abs(silence_before) > 0.01:
                logger.debug(f"🎵 AUDIO SYNC: Step {i+1} - current_time ({current_time:.2f}s) is past audio_start ({actual_audio_start:.2f}s), continuing from current_time")
        
        # Add audio file (or silence file if no audio)
        # No cutting - audio plays to completion
        concat_files.append(audio_path)
        
        # Update current_time based on what was actually added
        if has_audio:
            # Audio was added - current_time should be at actual_audio_start, then add duration
            current_time = actual_audio_start + audio_duration
            logger.info(f"🎵 AUDIO SYNC: Step {i+1} audio ends at {current_time:.2f}s")
        else:
            # Step without audio - the audio_path is a silence file with duration step_duration
            # The silence file represents the step duration in the video
            # Advance current_time by the step duration, but ensure we're at least at the step end in video timeline
            step_end_in_video = video_start_time + step_duration
            # The silence file was already added, so advance by its duration
            current_time = max(current_time + step_duration, step_end_in_video)
            logger.info(f"🎵 AUDIO SYNC: Step {i+1} has no audio - current_time advances to {current_time:.2f}s")
    
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

