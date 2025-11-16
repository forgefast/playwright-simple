#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video processor module.

Coordinates complete video processing: subtitles, audio, and cleanup.
"""

import logging
import re
import shutil
from pathlib import Path
from typing import List, Any, Optional

from .subtitles import SubtitleGenerator
from .audio_embedder import AudioEmbedder

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Coordinates video processing: subtitles, audio embedding, and cleanup."""
    
    def __init__(self, steps: List[Any], video_config):
        """
        Initialize video processor.
        
        Args:
            steps: List of TestStep objects or dicts with timing information
            video_config: VideoConfig object with video settings
        """
        self.steps = steps
        self.video_config = video_config
        self.subtitle_generator = SubtitleGenerator(steps, video_config)
        self.audio_embedder = AudioEmbedder(steps, video_config)
    
    async def process_video(self, video_path: Path, test_name: str) -> Optional[Path]:
        """
        Process video: add subtitles and audio in sequence.
        
        Args:
            video_path: Path to video file
            test_name: Name of test (for audio filename)
            
        Returns:
            Path to processed video, or original path if processing failed
        """
        current_video_path = video_path
        
        # Step 1: Generate and add subtitles if enabled
        if self.video_config.subtitles and self.steps:
            logger.info("🎬 Generating subtitles for video...")
            logger.info(f"🎬 DEBUG: steps count: {len(self.steps)}")
            print(f"📝 Gerando legendas para o vídeo...")
            print(f"📝 DEBUG: {len(self.steps)} steps com timestamps")
            try:
                result_video = await self.subtitle_generator.generate_and_add_subtitles(current_video_path)
                if result_video and result_video.exists():
                    current_video_path = result_video
                    logger.info(f"Video with subtitles ready: {current_video_path.name}")
                    print(f"✅ Vídeo com legendas pronto: {current_video_path.name}")
                    print(f"✅ DEBUG: Vídeo final: {current_video_path.resolve()}")
                else:
                    logger.warning(f"⚠️  DEBUG: result_video is None or doesn't exist: {result_video}")
                    print(f"⚠️  DEBUG: Vídeo com legendas não foi gerado corretamente")
            except Exception as e:
                logger.warning(f"Error generating subtitles: {e}", exc_info=True)
                print(f"⚠️  Erro ao gerar legendas: {e}")
                import traceback
                print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
        
        # Step 2: Generate and add audio narration if enabled
        # Use current_video_path (which may already have subtitles embedded)
        if (self.video_config.audio or self.video_config.narration) and self.steps:
            logger.info("🎤 Generating audio narration for video...")
            logger.info(f"🎤 DEBUG: steps count: {len(self.steps)}")
            logger.info(f"🎤 DEBUG: video_config.audio={self.video_config.audio}, video_config.narration={self.video_config.narration}")
            print(f"🔊 Gerando narração de áudio para o vídeo...")
            print(f"🔊 DEBUG: {len(self.steps)} steps com timestamps")
            print(f"🔊 DEBUG: audio={self.video_config.audio}, narration={self.video_config.narration}")
            try:
                logger.info(f"🎤 DEBUG: Using test_name: {test_name}")
                print(f"🔊 DEBUG: Nome do teste: {test_name}")
                result_video = await self.audio_embedder.generate_and_add_audio(current_video_path, test_name)
                if result_video and result_video.exists():
                    current_video_path = result_video
                    logger.info(f"Video with audio ready: {current_video_path.name}")
                    print(f"✅ Vídeo com áudio pronto: {current_video_path.name}")
                    print(f"✅ DEBUG: Vídeo final: {current_video_path.resolve()}")
                else:
                    logger.warning(f"⚠️  DEBUG: result_video is None or doesn't exist: {result_video}")
                    print(f"⚠️  DEBUG: Vídeo com áudio não foi gerado corretamente")
            except Exception as e:
                logger.warning(f"Error generating audio: {e}", exc_info=True)
                print(f"⚠️  Erro ao gerar áudio: {e}")
                import traceback
                print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
        
        return current_video_path
    
    async def cleanup_temp_files(self, video_dir: Path, test_name: str):
        """
        Clean up temporary files (SRT, MP3, intermediate videos) leaving only final MP4.
        
        Args:
            video_dir: Directory containing video files
            test_name: Name of test (to identify final video)
        """
        try:
            # Find final video (should be MP4 with test name)
            final_video = video_dir / f"{test_name}.mp4"
            if not final_video.exists():
                # Try to find any MP4 file as final
                mp4_files = list(video_dir.glob("*.mp4"))
                if mp4_files:
                    final_video = max(mp4_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Using most recent MP4 as final video: {final_video.name}")
            
            # Clean up temporary files
            cleaned = []
            
            # Remove SRT files
            for srt_file in video_dir.glob("*.srt"):
                try:
                    srt_file.unlink()
                    cleaned.append(srt_file.name)
                    logger.debug(f"Removed SRT: {srt_file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove SRT {srt_file.name}: {e}")
            
            # Remove MP3 files (narration audio)
            for mp3_file in video_dir.glob("*.mp3"):
                try:
                    mp3_file.unlink()
                    cleaned.append(mp3_file.name)
                    logger.debug(f"Removed MP3: {mp3_file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove MP3 {mp3_file.name}: {e}")
            
            # Remove intermediate video files (webm, _with_subtitles, _with_audio, etc.)
            for video_file in video_dir.glob("*"):
                if video_file.is_file():
                    # Skip final video
                    if video_file == final_video:
                        continue
                    
                    # Remove webm files (intermediate)
                    if video_file.suffix == '.webm':
                        try:
                            video_file.unlink()
                            cleaned.append(video_file.name)
                            logger.debug(f"Removed intermediate video: {video_file.name}")
                        except Exception as e:
                            logger.warning(f"Could not remove video {video_file.name}: {e}")
                    
                    # Remove files with temporary suffixes
                    if any(suffix in video_file.stem for suffix in ['_with_subtitles', '_with_audio', '_tts_temp']):
                        try:
                            video_file.unlink()
                            cleaned.append(video_file.name)
                            logger.debug(f"Removed temporary file: {video_file.name}")
                        except Exception as e:
                            logger.warning(f"Could not remove temporary file {video_file.name}: {e}")
            
            # Remove temporary TTS directories
            for temp_dir in video_dir.glob("*_tts_temp"):
                if temp_dir.is_dir():
                    try:
                        shutil.rmtree(temp_dir)
                        cleaned.append(temp_dir.name)
                        logger.debug(f"Removed temporary TTS directory: {temp_dir.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove TTS directory {temp_dir.name}: {e}")
            
            # Clean up old videos with hash-based names (after renaming)
            video_extensions = ['.webm', '.mp4']
            all_videos_after = []
            for ext in video_extensions:
                all_videos_after.extend(list(video_dir.glob(f"*{ext}")))
            
            for video_file in all_videos_after:
                if video_file == final_video:
                    continue
                
                video_name = video_file.stem
                is_hash_based = re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-', video_name)
                is_technical = len(video_name) < 10 and not any(c.isalpha() for c in video_name[:5])
                
                if is_hash_based or is_technical:
                    try:
                        video_file.unlink()
                        logger.debug(f"Deleted old video: {video_file.name}")
                    except Exception as e:
                        logger.warning(f"Error deleting old video {video_file.name}: {e}")
            
            if cleaned:
                logger.info(f"Cleaned up {len(cleaned)} temporary files")
                print(f"🧹 Limpeza: {len(cleaned)} arquivos temporários removidos")
            else:
                logger.debug("No temporary files to clean up")
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}", exc_info=True)

