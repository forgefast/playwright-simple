#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio processing module.

Handles audio mixing and TTS narration generation.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Any

from ..config import TestConfig
from ..exceptions import VideoProcessingError, TTSGenerationError
from ..tts import TTSManager

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio processing operations."""
    
    def __init__(self, config: TestConfig):
        """
        Initialize audio processor.
        
        Args:
            config: Test configuration
        """
        self.config = config
    
    async def generate_narration(
        self,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        output_dir: Path,
        test_name: str
    ) -> Optional[Path]:
        """
        Generate TTS narration from test steps.
        
        Args:
            test_steps: List of test steps
            output_dir: Directory to save narration
            test_name: Name of test
            
        Returns:
            Path to narration audio file, or None if generation failed
        """
        try:
            tts_manager = TTSManager(
                lang=self.config.video.narration_lang,
                engine=self.config.video.narration_engine,
                slow=self.config.video.narration_slow,
                voice=getattr(self.config.video, 'narration_voice', None)
            )
            
            narration_audio = await tts_manager.generate_narration(
                test_steps,
                output_dir,
                test_name
            )
            
            return narration_audio
        except ImportError as e:
            logger.error(f"TTS library not available: {e}")
            print(f"  ⚠️  {e}")
            print(f"  💡 Instale a biblioteca TTS: pip install gtts")
            return None
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating narration: {e}", exc_info=True)
            raise TTSGenerationError(f"Failed to generate narration: {e}") from e
    
    async def add_to_video(self, video_path: Path, audio_file: str) -> Optional[Path]:
        """
        Add audio track to video using ffmpeg.
        
        Args:
            video_path: Path to video file
            audio_file: Path to audio file (mp3, wav, etc.)
            
        Returns:
            Path to video with audio, or original path if processing failed
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            print(f"  ⚠️  Arquivo de áudio não encontrado: {audio_file}")
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Áudio não será adicionado.")
            return video_path
        
        output_path = video_path.parent / f"{video_path.stem}_with_audio{video_path.suffix}"
        
        try:
            # Mix audio with video (loop audio if shorter than video)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-stream_loop', '-1',  # Loop audio if needed
                '-i', str(audio_path),
                '-c:v', 'copy',  # Copy video as-is
                '-c:a', 'libopus' if video_path.suffix == '.webm' else 'aac',
                '-shortest',  # End when shortest stream ends
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and output_path.exists():
                video_path.unlink()
                output_path.rename(video_path)
                return video_path
            else:
                print(f"  ⚠️  Erro ao adicionar áudio: {result.stderr[:200]}")
                return video_path
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process audio: {e}") from e

