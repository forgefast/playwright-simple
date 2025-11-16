#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Utilities.

Provides utility functions for audio processing, duration calculation, and playback.
"""

import asyncio
import logging
import platform
import subprocess
from pathlib import Path

from ..exceptions import TTSGenerationError

logger = logging.getLogger(__name__)


def get_audio_duration(audio_path: Path) -> float:
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


def create_silence_file(output_path: Path, duration: float) -> bool:
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


async def play_audio_file(audio_file: Path) -> None:
    """
    Play audio file using system player.
    
    Tries multiple methods:
    1. ffplay (from ffmpeg) - best quality
    2. aplay (Linux) - for WAV files
    3. paplay (PulseAudio) - Linux
    4. afplay (macOS)
    5. cmdmp3 (Windows)
    
    Args:
        audio_file: Path to audio file to play
    """
    system = platform.system().lower()
    
    # Try ffplay first (best quality, works on all platforms)
    try:
        result = subprocess.run(
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', str(audio_file)],
            timeout=300,
            capture_output=True
        )
        if result.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try platform-specific players
    if system == 'linux':
        # Try aplay (for WAV) or paplay
        for player in ['paplay', 'aplay']:
            try:
                result = subprocess.run(
                    [player, str(audio_file)],
                    timeout=300,
                    capture_output=True
                )
                if result.returncode == 0:
                    return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    elif system == 'darwin':  # macOS
        try:
            result = subprocess.run(
                ['afplay', str(audio_file)],
                timeout=300,
                capture_output=True
            )
            if result.returncode == 0:
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    elif system == 'windows':
        try:
            result = subprocess.run(
                ['cmdmp3', str(audio_file)],
                timeout=300,
                capture_output=True
            )
            if result.returncode == 0:
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    # Fallback: if no player found, just wait estimated duration
    logger.warning(f"No audio player found. Audio playback skipped for: {audio_file.name}")
    duration = get_audio_duration(audio_file)
    if duration > 0:
        await asyncio.sleep(duration)

