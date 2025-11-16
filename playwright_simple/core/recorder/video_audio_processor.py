#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video and audio processor for YAML steps.

Handles generation of subtitles, audio, and embedding into video.
"""

import asyncio
import logging
import subprocess
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class VideoAudioProcessor:
    """Processes video with subtitles and audio."""
    
    def __init__(self, video_config, steps: List[Any]):
        """
        Initialize processor.
        
        Args:
            video_config: Video configuration object
            steps: List of TestStep objects or dicts with step data
        """
        self.video_config = video_config
        self.steps = steps
        self._hw_accel = self._detect_hardware_acceleration()
    
    def _detect_hardware_acceleration(self) -> Optional[str]:
        """Detect available hardware acceleration."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                system = platform.system().lower()
                
                # Check for hardware encoders
                if system == 'linux':
                    if 'h264_nvenc' in output:
                        return 'h264_nvenc'  # NVIDIA
                    elif 'h264_vaapi' in output:
                        return 'h264_vaapi'  # Intel/AMD VAAPI
                    elif 'h264_v4l2m2m' in output:
                        return 'h264_v4l2m2m'  # Video4Linux2
                elif system == 'darwin':  # macOS
                    if 'h264_videotoolbox' in output:
                        return 'h264_videotoolbox'  # VideoToolbox
                elif system == 'windows':
                    if 'h264_nvenc' in output:
                        return 'h264_nvenc'  # NVIDIA
                    elif 'h264_qsv' in output:
                        return 'h264_qsv'  # Intel QuickSync
        except:
            pass
        return None
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def generate_srt_file(self, video_path: Path) -> Optional[Path]:
        """Generate SRT subtitle file from steps."""
        if not self.steps:
            logger.warning("No steps available for subtitle generation")
            logger.warning(f"DEBUG: steps is {self.steps}")
            return None
        
        from ..step import TestStep
        
        logger.info(f"DEBUG: Generating SRT from {len(self.steps)} steps")
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        min_duration = 0.5
        gap = 0.1
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                processed_steps = []
                
                for step in self.steps:
                    if isinstance(step, TestStep):
                        step_start = step.start_time_seconds
                        step_end = step.end_time_seconds
                        step_duration = step.duration_seconds or (step_end - step_start)
                        step_text = step.subtitle
                    else:
                        # Fallback for dict compatibility
                        step_start = step.get('start_time', 0) if isinstance(step, dict) else 0
                        step_end = step.get('end_time', step_start + 1.0) if isinstance(step, dict) else step_start + 1.0
                        step_duration = step_end - step_start
                        step_text = step.get('subtitle') if isinstance(step, dict) else None
                    
                    if not step_text:
                        continue
                    
                    if step_duration < min_duration:
                        step_end = step_start + min_duration
                        step_duration = min_duration
                    
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'duration': step_duration
                    })
                
                # Adjust for continuity
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    next_different_index = None
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['text'] != current['text']:
                            next_different_index = j
                            break
                    
                    if next_different_index is not None:
                        next_step = processed_steps[next_different_index]
                        current['end'] = next_step['start'] - gap
                        current['duration'] = current['end'] - current['start']
                
                # Prevent overlaps
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['start'] <= current['end']:
                            new_end = next_step['start'] - gap
                            new_end = max(current['start'] + 0.1, new_end)
                            current['end'] = new_end
                            current['duration'] = new_end - current['start']
                            break
                
                # Write SRT entries
                for step in processed_steps:
                    if step['end'] > step['start'] and step['text']:
                        start_str = self._format_srt_time(step['start'])
                        end_str = self._format_srt_time(step['end'])
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_str} --> {end_str}\n")
                        f.write(f"{step['text']}\n\n")
                        subtitle_index += 1
            
            if srt_path.exists():
                logger.info(f"SRT file generated: {srt_path}")
                return srt_path
            return None
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            return None
    
    async def generate_and_add_subtitles(self, video_path: Path) -> Optional[Path]:
        """Generate SRT file and add subtitles to video."""
        logger.info(f"DEBUG: generate_and_add_subtitles called with {len(self.steps)} steps")
        srt_path = await self.generate_srt_file(video_path)
        if not srt_path or not srt_path.exists():
            logger.warning("SRT file not generated, skipping subtitle processing")
            logger.warning(f"DEBUG: srt_path={srt_path}, exists={srt_path.exists() if srt_path else False}")
            return video_path
        
        if not self.video_config.hard_subtitles:
            logger.info("Hard subtitles disabled, SRT file generated but not embedded")
            return video_path
        
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found, cannot embed subtitles")
            return video_path
        
        output_path = video_path.parent / f"{video_path.stem}.mp4"
        if output_path == video_path and video_path.suffix == '.mp4':
            output_path = video_path.parent / f"{video_path.stem}_with_subtitles.mp4"
        
        output_path = output_path.resolve()
        
        try:
            video_absolute = str(video_path.resolve())
            srt_absolute = str(srt_path.resolve())
            simple_srt_name = "subtitles_temp.srt"
            simple_srt_path = video_path.parent / simple_srt_name
            
            try:
                shutil.copy2(srt_path, simple_srt_path)
                filter_expr = f"subtitles={simple_srt_name}:force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,
                    '-vf', filter_expr,
                ]
            except Exception as e:
                logger.warning(f"Error copying SRT: {e}")
                srt_for_filter = srt_absolute.replace('\\', '/')
                srt_escaped = srt_for_filter.replace(' ', '\\ ').replace(':', '\\:').replace('[', '\\[').replace(']', '\\]').replace("'", "\\'")
                filter_expr = f"subtitles='{srt_escaped}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,
                    '-vf', filter_expr,
                ]
                simple_srt_path = None
            
            if output_path.suffix == '.mp4' or self.video_config.codec == 'mp4':
                # When adding subtitles, we need to re-encode the video
                # Use software encoding (libx264) for better compatibility with subtitle filter
                # Hardware acceleration may not work well with subtitle filters
                # IMPORTANT: Map only video stream, ignore any existing audio (audio will be added later)
                cmd.extend([
                    '-map', '0:v:0',  # Map only video stream, ignore audio
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '23',
                    '-an',  # Disable audio - we'll add it later
                    '-movflags', '+faststart',
                ])
                logger.info("Using software encoding (libx264) for subtitle embedding (audio disabled - will be added later)")
            
            cmd.extend(['-y', str(output_path)])
            
            logger.info(f"DEBUG: Embedding subtitles - video: {video_path.name}, srt: {srt_path.name}")
            logger.info(f"DEBUG: ffmpeg command (first 10 args): {' '.join(cmd[:10])}...")
            
            result = subprocess.run(
                cmd,
                cwd=str(video_path.parent),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if simple_srt_path and simple_srt_path.exists():
                try:
                    simple_srt_path.unlink()
                except:
                    pass
            
            if result.returncode == 0 and output_path.exists():
                if video_path.exists() and video_path != output_path:
                    video_path.unlink()
                if output_path != video_path:
                    output_path.rename(video_path)
                if srt_path.exists():
                    try:
                        srt_path.unlink()
                    except:
                        pass
                logger.info(f"Video processed with subtitles: {video_path.name}")
                return video_path
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                logger.error(f"ffmpeg failed to embed subtitles (returncode={result.returncode})")
                logger.error(f"ffmpeg stderr: {error_msg[:2000] if error_msg else 'No error message'}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
        except Exception as e:
            logger.error(f"Error processing video with subtitles: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            return video_path
    
    async def generate_and_add_audio(self, video_path: Path, test_name: str) -> Optional[Path]:
        """Generate audio narration and add to video."""
        logger.info(f"DEBUG: generate_and_add_audio called with {len(self.steps)} steps")
        if not self.steps:
            logger.warning("No steps available for audio generation")
            logger.warning(f"DEBUG: steps is {self.steps}")
            return video_path
        
        try:
            from ..tts import TTSManager
        except ImportError:
            logger.warning("TTSManager not available, skipping audio generation")
            return video_path
        
        use_audio_config = self.video_config.audio
        if use_audio_config:
            lang = self.video_config.audio_lang
            engine = self.video_config.audio_engine
            voice = getattr(self.video_config, 'audio_voice', None)
            rate = getattr(self.video_config, 'audio_rate', None)
            pitch = getattr(self.video_config, 'audio_pitch', None)
            volume = getattr(self.video_config, 'audio_volume', None)
        else:
            lang = self.video_config.narration_lang
            engine = self.video_config.narration_engine
            voice = getattr(self.video_config, 'narration_voice', None)
            rate = None
            pitch = None
            volume = None
        
        if not engine or engine == 'gtts':
            engine = 'edge-tts'
        
        try:
            try:
                import edge_tts
                edge_tts_available = True
            except ImportError:
                edge_tts_available = False
                logger.warning("edge-tts not available, cannot generate audio")
                return video_path
            except Exception as e:
                logger.error(f"Error importing edge-tts: {e}", exc_info=True)
                return video_path
            
            tts_manager = TTSManager(
                lang=lang,
                engine=engine,
                slow=False,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            
            # Pass steps directly to TTSManager - it now handles TestStep objects
            from ..step import TestStep
            
            steps_with_audio_text = sum(1 for s in self.steps if isinstance(s, TestStep) and s.audio and s.audio.strip())
            if steps_with_audio_text == 0:
                logger.warning("No steps with audio text found")
                return video_path
            
            narration_audio = await tts_manager.generate_narration(
                self.steps,
                video_path.parent,
                test_name,
                return_timed_audio=True
            )
            
            if not narration_audio or not narration_audio.exists():
                logger.warning("Audio narration generation failed")
                return video_path
            
            logger.info(f"Audio narration generated: {narration_audio.name}")
            
            # Embed audio into video
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("ffmpeg not found, cannot embed audio")
                return video_path
            
            if video_path.suffix == '.mp4':
                output_path = video_path.parent / f"{video_path.stem}_with_audio.mp4"
            else:
                output_path = video_path.parent / f"{video_path.stem}.mp4"
            
            output_path = output_path.resolve()
            video_input_absolute = str(video_path.resolve())
            audio_input_absolute = str(narration_audio.resolve())
            
            logger.info(f"DEBUG: Input video: {video_input_absolute}")
            logger.info(f"DEBUG: Input audio: {audio_input_absolute}")
            logger.info(f"DEBUG: Output video: {output_path}")
            
            if not video_path.exists() or not narration_audio.exists():
                logger.error(f"Video or audio file does not exist - video: {video_path.exists()}, audio: {narration_audio.exists()}")
                return video_path
            
            # Build command - copy video stream (no re-encoding needed when just adding audio)
            # Use -map to explicitly select streams and ignore any existing audio in video
            # Important: Map video first, then audio, to ensure correct stream selection
            # Boost volume and normalize audio for better playback
            cmd = [
                'ffmpeg',
                '-i', video_input_absolute,  # Input 0: video (should have no audio after subtitle processing)
                '-i', audio_input_absolute,   # Input 1: audio narration
                '-map', '0:v:0',             # Map ONLY video stream from first input
                '-map', '1:a:0',             # Map audio stream from second input (narration)
                '-c:v', 'copy',              # Copy video stream without re-encoding
                '-af', 'volume=3.0,aresample=44100',  # Boost volume 3x (9.5dB) and resample to 44.1kHz
                '-c:a', 'aac',                # Encode audio as AAC
                '-b:a', '128k',               # Audio bitrate
                '-ac', '2',                   # Set audio to stereo (2 channels)
                '-shortest',                  # Finish encoding when shortest input stream ends
                '-movflags', '+faststart',    # Optimize for streaming
                '-y',                         # Overwrite output file
                str(output_path)
            ]
            
            # Verify input files exist
            if not video_path.exists():
                logger.error(f"Video file does not exist: {video_path}")
                return video_path
            if not narration_audio.exists():
                logger.error(f"Audio file does not exist: {narration_audio}")
                return video_path
            
            logger.info(f"DEBUG: Embedding audio - video: {video_path.name}, audio: {narration_audio.name}")
            logger.info(f"DEBUG: ffmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=str(video_path.parent),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0 and output_path.exists():
                output_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Video with audio created: {output_path.name} ({output_size:.1f} MB)")
                
                # Verify audio was actually added
                try:
                    verify_result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', str(output_path)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if verify_result.returncode == 0 and verify_result.stdout.strip():
                        logger.info(f"✅ Verified: Audio stream exists in output file (codec: {verify_result.stdout.strip()})")
                    else:
                        logger.warning(f"⚠️  Warning: No audio stream found in output file!")
                except Exception as e:
                    logger.warning(f"Could not verify audio in output file: {e}")
                
                # Replace original if needed
                if video_path.exists() and video_path != output_path:
                    logger.info(f"Removing original video (without audio): {video_path.name}")
                    video_path.unlink()
                if output_path != video_path:
                    logger.info(f"Renaming {output_path.name} to {video_path.name}")
                    output_path.rename(video_path)
                    logger.info(f"✅ Final video with audio: {video_path.name}")
                else:
                    logger.info(f"✅ Video with audio already has correct name: {video_path.name}")
                
                return video_path
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                logger.error(f"ffmpeg failed to embed audio (returncode={result.returncode})")
                logger.error(f"ffmpeg stderr: {error_msg[:2000] if error_msg else 'No error message'}")
                logger.error(f"ffmpeg stdout: {result.stdout[:2000] if result.stdout else 'No output'}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
                
        except Exception as e:
            logger.error(f"Error generating and adding audio: {e}", exc_info=True)
            return video_path

