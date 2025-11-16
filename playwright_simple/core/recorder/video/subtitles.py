#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle generation module.

Provides functionality for generating SRT subtitle files and embedding them in videos.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Any

logger = logging.getLogger(__name__)


def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SubtitleGenerator:
    """Generates SRT subtitle files and embeds them in videos."""
    
    def __init__(self, steps: List[Any], video_config):
        """
        Initialize subtitle generator.
        
        Args:
            steps: List of TestStep objects or dicts with timing information
            video_config: VideoConfig object with subtitle settings
        """
        self.steps = steps
        self.video_config = video_config
    
    async def generate_srt_file(self, video_path: Path) -> Optional[Path]:
        """
        Generate SRT subtitle file from step timestamps.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to SRT file, or None if generation failed
        """
        logger.info(f"🎬 DEBUG: generate_srt_file called")
        logger.info(f"🎬 DEBUG: hasattr steps: {hasattr(self, 'steps')}")
        if hasattr(self, 'steps'):
            logger.info(f"🎬 DEBUG: steps is not None: {self.steps is not None}")
            if self.steps:
                logger.info(f"🎬 DEBUG: steps length: {len(self.steps)}")
            else:
                logger.warning(f"🎬 DEBUG: steps is EMPTY list!")
        else:
            logger.warning(f"🎬 DEBUG: steps attribute does NOT exist!")
        
        if not self.steps:
            logger.warning("No steps available for subtitle generation")
            print(f"⚠️  DEBUG: Não há steps para gerar SRT")
            return None
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        min_duration = 0.5  # Minimum subtitle duration in seconds
        gap = 0.1  # Gap between subtitles to prevent overlap
        
        try:
            from ...step import TestStep
        except ImportError:
            TestStep = None
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                
                # Process steps and eliminate overlaps
                processed_steps = []
                logger.info(f"🎬 DEBUG: Processing {len(self.steps)} steps for SRT")
                steps_with_subtitle = 0
                steps_without_subtitle = 0
                
                for step in self.steps:
                    if isinstance(step, TestStep):
                        step_start = step.start_time_seconds
                        step_end = step.end_time_seconds
                        step_duration = step.duration_seconds or (step_end - step_start)
                    else:
                        # Fallback for dict compatibility
                        step_start = step.get('start_time', 0) if isinstance(step, dict) else 0
                        step_end = step.get('end_time', step_start + 1.0) if isinstance(step, dict) else step_start + 1.0
                        step_duration = step_end - step_start
                    
                    # Get text from step (use subtitle field, not description)
                    if isinstance(step, TestStep):
                        step_text = step.subtitle
                        step_action = list(step.action.keys())[0] if step.action else 'unknown'
                    else:
                        step_text = step.get('subtitle') if isinstance(step, dict) else None
                        step_action = step.get('action', 'unknown') if isinstance(step, dict) else 'unknown'
                    
                    if not step_text:
                        # If no subtitle, skip this step (for continuity, we only show steps with subtitles)
                        steps_without_subtitle += 1
                        logger.debug(f"🎬 DEBUG: Skipping step without subtitle: action={step_action}, start={step_start:.2f}s")
                        continue
                    
                    steps_with_subtitle += 1
                    logger.debug(f"🎬 DEBUG: Processing step with subtitle: '{step_text}', start={step_start:.2f}s, end={step_end:.2f}s")
                    
                    # Ensure minimum duration
                    if step_duration < min_duration:
                        step_end = step_start + min_duration
                        step_duration = min_duration
                    
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'duration': step_duration
                    })
                
                # Adjust end times for subtitle continuity
                # If a step has a subtitle and the next step doesn't have one (or has same),
                # extend current subtitle until next step with different subtitle
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    # Find next step with a different subtitle (or end of list)
                    next_different_index = None
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['text'] != current['text']:
                            next_different_index = j
                            break
                    
                    if next_different_index is not None:
                        # Extend current subtitle until next different subtitle starts
                        next_step = processed_steps[next_different_index]
                        current['end'] = next_step['start'] - gap
                        current['duration'] = current['end'] - current['start']
                    # If no next different subtitle, keep original end time
                
                # Adjust end times to prevent overlaps (after continuity extension)
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    # Find next step that starts before this one ends
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['start'] <= current['end']:
                            # Adjust current end to be before next start
                            new_end = next_step['start'] - gap
                            new_end = max(current['start'] + 0.1, new_end)  # Minimum 0.1s visibility
                            current['end'] = new_end
                            current['duration'] = new_end - current['start']
                            break
                
                logger.info(f"🎬 DEBUG: Steps with subtitle: {steps_with_subtitle}, without subtitle: {steps_without_subtitle}")
                logger.info(f"🎬 DEBUG: Processed {len(processed_steps)} steps for SRT file")
                
                # Write SRT entries
                srt_entries_written = 0
                for step in processed_steps:
                    if step['end'] > step['start'] and step['text']:
                        start_str = format_srt_time(step['start'])
                        end_str = format_srt_time(step['end'])
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_str} --> {end_str}\n")
                        f.write(f"{step['text']}\n\n")
                        subtitle_index += 1
                        srt_entries_written += 1
                
                logger.info(f"🎬 DEBUG: Wrote {srt_entries_written} SRT entries to file")
            
            if srt_path.exists():
                srt_size = srt_path.stat().st_size
                logger.info(f"SRT file generated: {srt_path} ({srt_size} bytes)")
                print(f"✅ DEBUG: Arquivo SRT gerado: {srt_path.name} ({srt_size} bytes)")
            else:
                logger.warning(f"⚠️  DEBUG: SRT file was NOT created: {srt_path}")
                print(f"⚠️  DEBUG: Arquivo SRT NÃO foi criado: {srt_path}")
            
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            return None
    
    async def generate_and_add_subtitles(self, video_path: Path) -> Optional[Path]:
        """
        Generate SRT file and add subtitles to video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to video with subtitles, or original path if processing failed
        """
        # Generate SRT file
        srt_path = await self.generate_srt_file(video_path)
        if not srt_path or not srt_path.exists():
            logger.warning("SRT file not generated, skipping subtitle processing")
            return video_path
        
        # Check if hard_subtitles is enabled
        if not self.video_config.hard_subtitles:
            logger.info("Hard subtitles disabled, SRT file generated but not embedded")
            print(f"📝 Arquivo SRT gerado: {srt_path.name} (não queimado no vídeo)")
            return video_path
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found, cannot embed subtitles")
            print(f"⚠️  ffmpeg não encontrado. Legendas não serão queimadas no vídeo.")
            return video_path
        
        # Process video with ffmpeg to embed subtitles
        # Always output as MP4 to ensure compatibility
        output_path = video_path.parent / f"{video_path.stem}.mp4"
        if output_path == video_path and video_path.suffix == '.mp4':
            # If same path, use _with_subtitles suffix temporarily
            output_path = video_path.parent / f"{video_path.stem}_with_subtitles.mp4"
        
        # Ensure output_path is absolute
        output_path = output_path.resolve()
        
        try:
            # Escape SRT filename for ffmpeg filter
            srt_filename = srt_path.name
            srt_escaped = srt_filename.replace(':', '\\:').replace('[', '\\[').replace(']', '\\]').replace("'", "\\'")
            
            # Determine codec based on output file extension or config
            output_ext = output_path.suffix.lower()
            if output_ext == '.mp4' or self.video_config.codec == 'mp4':
                video_codec = 'libx264'
                audio_codec = 'aac'  # MP4 requires AAC audio
            else:
                video_codec = 'libvpx-vp9'
                audio_codec = 'copy'
            
            # Build ffmpeg command to burn subtitles into video
            # Strategy: Use a simple filename approach to avoid path escaping issues
            # Copy SRT to a simple name in the same directory as video
            video_absolute = str(video_path.resolve())
            srt_absolute = str(srt_path.resolve())
            
            # Create a temporary SRT with a simple name (no spaces, no special chars)
            simple_srt_name = "subtitles_temp.srt"
            simple_srt_path = video_path.parent / simple_srt_name
            srt_escaped_absolute = None  # Initialize to avoid UnboundLocalError
            
            try:
                # Copy SRT to simple filename
                shutil.copy2(srt_path, simple_srt_path)
                logger.info(f"🎬 DEBUG: SRT copiado para nome simples: {simple_srt_name}")
                
                # Use simple filename in filter (relative to video directory)
                # This avoids all path escaping issues
                filter_expr = f"subtitles={simple_srt_name}:force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,  # Use absolute path for video input
                    '-vf', filter_expr,
                ]
            except Exception as e:
                logger.warning(f"⚠️  Erro ao copiar SRT: {e}")
                # Fallback: try with absolute path (may fail with special chars)
                srt_for_filter = srt_absolute.replace('\\', '/')
                srt_escaped_absolute = srt_for_filter.replace(' ', '\\ ').replace(':', '\\:').replace('[', '\\[').replace(']', '\\]').replace("'", "\\'")
                filter_expr = f"subtitles='{srt_escaped_absolute}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,
                    '-vf', filter_expr,
                ]
                simple_srt_path = None  # Don't try to clean up
            
            # Always use MP4 codecs for output
            # Otimização: usar preset 'ultrafast' para codificação mais rápida
            if output_ext == '.mp4' or self.video_config.codec == 'mp4':
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Otimização: codificação mais rápida
                    '-crf', '23',  # Qualidade razoável (18-28 é aceitável, 23 é padrão)
                    '-c:a', 'aac',
                    '-b:a', '128k',  # Otimização: bitrate de áudio reduzido
                    '-movflags', '+faststart',
                ])
            else:
                cmd.extend([
                    '-c:v', video_codec,
                    '-c:a', audio_codec,
                ])
            
            cmd.extend([
                '-y',
                str(output_path)
            ])
            
            logger.info(f"Processing video with subtitles: {srt_path.name}")
            logger.info(f"🎬 DEBUG: SRT path (absolute): {srt_absolute}")
            if srt_escaped_absolute:
                logger.info(f"🎬 DEBUG: SRT path (escaped): {srt_escaped_absolute}")
            else:
                logger.info(f"🎬 DEBUG: SRT path (using simple filename): {simple_srt_name}")
            logger.info(f"🎬 DEBUG: Video input (absolute): {video_absolute}")
            logger.info(f"🎬 DEBUG: Video output: {output_path}")
            logger.info(f"🎬 DEBUG: FFmpeg command: {' '.join(cmd)}")
            print(f"🎬 Processando vídeo com legendas (burn)...")
            print(f"🎬 DEBUG: Queimando legendas do arquivo: {srt_path.name}")
            print(f"🎬 DEBUG: Vídeo de entrada: {video_path.name}")
            print(f"🎬 DEBUG: Vídeo de saída: {output_path.name}")
            
            # Use absolute path for output in command
            cmd_absolute = cmd[:-1] + [str(output_path)]  # Replace last element (output path) with absolute path
            
            result = subprocess.run(
                cmd_absolute,
                cwd=str(video_path.parent),  # Run from video directory (so simple_srt_name works)
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Clean up temporary SRT file (if we created one)
            if simple_srt_path and simple_srt_path.exists():
                try:
                    simple_srt_path.unlink()
                    logger.debug(f"🎬 DEBUG: Arquivo SRT temporário removido: {simple_srt_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Não foi possível remover SRT temporário: {e}")
            
            # Log ffmpeg output for debugging
            if result.returncode != 0:
                # Get full error message (stderr usually contains the actual error)
                error_output = result.stderr if result.stderr else result.stdout
                logger.warning(f"🎬 DEBUG: FFmpeg return code: {result.returncode}")
                logger.warning(f"🎬 DEBUG: FFmpeg stderr (full): {error_output}")
                logger.warning(f"🎬 DEBUG: FFmpeg stdout: {result.stdout}")
                print(f"⚠️  DEBUG: FFmpeg retornou código {result.returncode}")
                if error_output:
                    # Try to extract the actual error message (usually after version info)
                    error_lines = error_output.split('\n')
                    # Skip version info and find actual error
                    actual_error = '\n'.join([line for line in error_lines if line and not line.startswith('ffmpeg version') and not line.startswith('built with') and not line.startswith('configuration:')])
                    if actual_error:
                        print(f"⚠️  DEBUG: Erro FFmpeg: {actual_error[:500]}")
                    else:
                        print(f"⚠️  DEBUG: Erro FFmpeg completo: {error_output[:500]}")
                
            
            if result.returncode == 0 and output_path.exists():
                # Replace original video with subtitled version
                if video_path.exists() and video_path != output_path:
                    video_path.unlink()
                if output_path != video_path:
                    output_path.rename(video_path)
                # Clean up SRT file (subtitles are now embedded)
                if srt_path.exists():
                    try:
                        srt_path.unlink()
                        logger.debug(f"Cleaned up SRT file: {srt_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove SRT file: {e}")
                logger.info(f"Video processed with subtitles: {video_path.name}")
                print(f"✅ Vídeo processado com legendas embutidas: {video_path.name}")
                return video_path
            else:
                error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
                logger.warning(f"ffmpeg failed to embed subtitles: {error_msg}")
                print(f"⚠️  Erro ao processar vídeo com legendas")
                print(f"   Detalhes: {error_msg[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
        except Exception as e:
            logger.error(f"Error processing video with subtitles: {e}", exc_info=True)
            print(f"⚠️  Erro ao processar vídeo: {e}")
            if output_path.exists():
                output_path.unlink()
            return video_path

