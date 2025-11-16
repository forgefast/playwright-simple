#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step synchronizer for audio/video synchronization.

This module provides a centralized way to synchronize audio with video
by creating a concatenated audio file based on step timings and generated audio.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .step import TestStep
from .exceptions import TTSGenerationError

logger = logging.getLogger(__name__)


class StepSynchronizer:
    """
    Synchronizes audio with video based on step timings.
    
    This class takes a list of TestStep objects with generated audio
    and creates a single concatenated audio file that is synchronized
    with the video timeline.
    """
    
    def __init__(self):
        """Initialize the step synchronizer."""
        pass
    
    async def synchronize_audio(
        self,
        steps: List[TestStep],
        output_path: Path,
        temp_dir: Path
    ) -> bool:
        """
        Synchronize audio files from steps into a single audio file.
        
        Args:
            steps: List of TestStep objects with audio_file_path and audio_duration_seconds set
            output_path: Path to save the synchronized audio file
            temp_dir: Temporary directory for intermediate files
            
        Returns:
            True if successful, False otherwise
        """
        if not steps:
            logger.warning("No steps provided for synchronization")
            return False
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"ffmpeg not found. Cannot synchronize audio: {e}")
            raise TTSGenerationError("ffmpeg is required for audio synchronization but was not found") from e
        
        # Sort steps by start time
        sorted_steps = sorted(steps, key=lambda s: s.start_time_seconds)
        
        # Build list of audio files and silence to concatenate
        concat_files = []
        silence_files = []
        current_time = 0.0
        
        logger.info(f"🎵 SYNC: Starting audio synchronization for {len(sorted_steps)} steps")
        
        for i, step in enumerate(sorted_steps, 1):
            step_start = step.start_time_seconds
            step_duration = step.duration_seconds or 0.0
            step_end = step.end_time_seconds
            
            # Add silence before step if needed
            silence_before = step_start - current_time
            if silence_before > 0.01:  # Only add silence if > 10ms
                silence_file = temp_dir / f"silence_before_{i}.mp3"
                if self._create_silence_file(silence_file, silence_before):
                    concat_files.append(silence_file)
                    silence_files.append(silence_file)
                    logger.debug(f"🎵 SYNC: Step {i} - Added {silence_before:.2f}s silence before")
                    current_time += silence_before
            elif silence_before < -0.01:
                logger.warning(f"🎵 SYNC: Step {i} - Warning: current_time ({current_time:.2f}s) is past step_start ({step_start:.2f}s)")
            
            # Add step audio if available
            if step.audio_file_path and step.audio_file_path.exists():
                audio_duration = step.audio_duration_seconds or 0.0
                if audio_duration > 0:
                    concat_files.append(step.audio_file_path)
                    current_time += audio_duration
                    logger.debug(f"🎵 SYNC: Step {i} - Added audio ({audio_duration:.2f}s) at {step_start:.2f}s")
                else:
                    logger.warning(f"🎵 SYNC: Step {i} - Audio file exists but duration is 0")
            else:
                # Step has no audio - add silence for step duration
                if step_duration > 0.01:
                    silence_file = temp_dir / f"silence_step_{i}.mp3"
                    if self._create_silence_file(silence_file, step_duration):
                        concat_files.append(silence_file)
                        silence_files.append(silence_file)
                        current_time += step_duration
                        logger.debug(f"🎵 SYNC: Step {i} - Added {step_duration:.2f}s silence (no audio)")
        
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
        
        logger.info(f"🎵 SYNC: Concatenating {len(concat_files)} audio files...")
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
            final_duration = self._get_audio_duration(output_path)
            logger.info(f"🎵 SYNC: Synchronized audio created: {output_path.name} ({final_duration:.2f}s)")
            return True
        else:
            error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
            logger.error(f"Failed to synchronize audio: {error_msg}")
            raise TTSGenerationError(f"Failed to synchronize audio: {error_msg}")
    
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

