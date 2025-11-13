#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle generation module.

Handles SRT file generation and subtitle embedding in videos.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime

from ..config import TestConfig
from ..exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Handles subtitle generation and embedding."""
    
    def __init__(self, config: TestConfig):
        """
        Initialize subtitle generator.
        
        Args:
            config: Test configuration
        """
        self.config = config
    
    def format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def generate(self, video_path: Path, test_steps: List[Any], start_time: datetime) -> Optional[Path]:
        """
        Generate SRT subtitle file from test steps.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps (TestStep objects or dicts with 'text', 'start_time', 'duration')
            start_time: Video start time (when context was created, when recording began)
            
        Returns:
            Path to SRT file, or None if generation failed or subtitles disabled
        """
        # Don't generate SRT if subtitles are disabled
        if not self.config.video.subtitles:
            return None
        
        if not test_steps:
            return None
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                # Convert TestStep objects to dicts for processing
                from ..step import TestStep
                step_dicts = []
                for step in test_steps:
                    if isinstance(step, TestStep):
                        step_dicts.append(step.to_dict())
                    elif isinstance(step, dict):
                        step_dicts.append(step)
                    else:
                        logger.warning(f"Unknown step type: {type(step)}, skipping")
                        continue
                
                # Sort steps by start time to ensure proper ordering
                sorted_steps = sorted(step_dicts, key=lambda s: s.get('start_time', 0))
                
                # Process steps and eliminate overlaps
                # Strategy: Build a timeline where each subtitle ends before the next one starts
                processed_steps = []
                subtitle_index = 1
                gap = 0.1  # 100ms gap between subtitles to prevent overlap
                min_duration = self.config.video.subtitle_min_duration  # Use config value (default: 0.5s)
                
                # First pass: calculate end times for all steps
                for i, step in enumerate(sorted_steps):
                    # Get timing from step (TestStep objects have start_time_seconds, end_time_seconds)
                    step_start = step.get('start_time', 0)
                    step_end = step.get('end_time')
                    step_duration = step.get('duration', 0)
                    
                    # If end_time is not provided, calculate from start + duration
                    if step_end is None:
                        step_end = step_start + step_duration
                    
                    # Priority: subtitle > text > description > auto-generated
                    step_text = step.get('subtitle') or step.get('text') or step.get('description', f'Passo {subtitle_index}')
                    
                    # Use actual duration, but ensure minimum for visibility (prevents glitches)
                    actual_duration = step_end - step_start
                    if actual_duration < min_duration:
                        # Extend end time to meet minimum duration
                        step_end = step_start + min_duration
                        actual_duration = min_duration
                    
                    # Store step with calculated end time
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'index': subtitle_index,
                        'duration': actual_duration
                    })
                    subtitle_index += 1
                
                # Second pass: adjust end times to prevent overlaps
                # Strategy: Iterate through all steps and ensure each ends before any subsequent step starts
                # Do multiple passes to handle cascading adjustments
                max_iterations = 10
                for iteration in range(max_iterations):
                    has_overlaps = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        
                        # Find the earliest subsequent step that starts while this one is active
                        earliest_next_start = None
                        for j in range(i + 1, len(processed_steps)):
                            next_step_start = processed_steps[j]['start']
                            # If next step starts before or at the same time as current step ends, we have overlap
                            # Use <= to catch edge cases where they're exactly equal
                            if next_step_start <= current_step['end']:
                                if earliest_next_start is None or next_step_start < earliest_next_start:
                                    earliest_next_start = next_step_start
                        
                        # If there's overlap, adjust end time to end just before the earliest overlapping step
                        if earliest_next_start is not None:
                            # End this subtitle just before the next one starts (with gap)
                            # Priority: prevent overlap over minimum duration
                            # If a step starts before this one ends, this one must end before it starts
                            new_end = earliest_next_start - gap
                            # But ensure it's at least a tiny bit visible (0.1s minimum)
                            new_end = max(current_step['start'] + 0.1, new_end)
                            # Always update if there's any change needed (even if new_end >= current_end, 
                            # we need to ensure it's before the next step)
                            if abs(new_end - current_step['end']) > 0.001:  # Use small epsilon for comparison
                                current_step['end'] = new_end
                                has_overlaps = True
                    
                    # If no overlaps were found, we're done
                    if not has_overlaps:
                        break
                
                # Final pass: ensure no overlaps remain (safety check)
                # Process multiple times to handle cascading adjustments
                for final_iteration in range(10):
                    made_changes = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        for j in range(i + 1, len(processed_steps)):
                            next_step = processed_steps[j]
                            # If there's still overlap (even by a tiny amount), force current step to end before next starts
                            # Use >= to catch edge cases
                            if current_step['end'] >= next_step['start']:
                                new_end = next_step['start'] - gap
                                # Ensure minimum visibility (but allow very short subtitles if needed to prevent overlap)
                                new_end = max(current_step['start'] + 0.05, new_end)  # Reduced to 50ms minimum
                                if abs(new_end - current_step['end']) > 0.001:  # Only update if there's a meaningful change
                                    current_step['end'] = new_end
                                    made_changes = True
                    if not made_changes:
                        break
                
                # Third pass: write subtitles (only those with valid duration)
                subtitle_index = 1
                for step in processed_steps:
                    if step['end'] > step['start']:
                        start_time_str = self.format_time(step['start'])
                        end_time_str = self.format_time(step['end'])
                        
                        # Write SRT entry
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time_str} --> {end_time_str}\n")
                        f.write(f"{step['text']}\n\n")
                        
                        subtitle_index += 1
            
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            print(f"  ⚠️  Erro ao gerar arquivo SRT: {e}")
            return None
    
    async def add_to_video(self, video_path: Path, test_steps: List[Dict[str, Any]], start_time: datetime) -> Optional[Path]:
        """
        Add subtitles to video using ffmpeg.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps
            start_time: Test start time
            
        Returns:
            Path to video with subtitles, or original path if processing failed
        """
        # Don't add subtitles if disabled
        if not self.config.video.subtitles:
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Legendas não serão adicionadas.")
            return video_path
        
        # Generate SRT file
        srt_path = await self.generate(video_path, test_steps, start_time)
        if not srt_path or not srt_path.exists():
            return video_path
        
        # Create output path
        output_path = video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}"
        
        try:
            # Use ffmpeg subtitles filter for proper SRT support
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', f"subtitles='{srt_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
                '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                '-c:a', 'copy',  # Copy audio as-is
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
                srt_path.unlink()  # Clean up SRT file
                return video_path
            else:
                # Fallback: try drawtext if subtitles filter fails
                print(f"  ⚠️  Tentando método alternativo para legendas...")
                return await self.add_drawtext(video_path, test_steps)
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.warning(f"Error processing subtitles, trying fallback method: {e}")
            print(f"  ⚠️  Erro ao processar legendas: {e}")
            if output_path.exists():
                output_path.unlink()
            return await self.add_drawtext(video_path, test_steps)
    
    async def add_drawtext(self, video_path: Path, test_steps: List[Dict[str, Any]]) -> Optional[Path]:
        """
        Add subtitles to video using ffmpeg drawtext filter (fallback method).
        
        This is used when the subtitles filter fails. Drawtext is less flexible
        but more compatible across different ffmpeg versions.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps with timing information
            
        Returns:
            Path to video with subtitles, or original path if processing failed
            
        Raises:
            VideoProcessingError: If video processing fails
        """
        output_path = video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}"
        
        try:
            # Build drawtext filters for each step
            drawtext_filters = []
            for i, step in enumerate(test_steps, 1):
                step_start = step.get('start_time', 0)
                step_duration = step.get('duration', 2.0)
                step_text = step.get('text', step.get('description', f'Passo {i}'))
                
                # Escape special characters for drawtext
                escaped_text = step_text.replace(':', '\\:').replace("'", "\\'").replace('[', '\\[').replace(']', '\\]')
                
                # Create drawtext filter for this step
                drawtext_filter = (
                    f"drawtext=text='{escaped_text}':"
                    f"fontsize=24:"
                    f"fontcolor=white:"
                    f"x=(w-text_w)/2:"
                    f"y=h-th-20:"
                    f"box=1:"
                    f"boxcolor=black@0.7:"
                    f"boxborderw=5:"
                    f"enable='between(t,{step_start},{step_start + step_duration})'"
                )
                drawtext_filters.append(drawtext_filter)
            
            # Combine all filters
            if drawtext_filters:
                filter_complex = ','.join(drawtext_filters)
                
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vf', filter_complex,
                    '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                    '-c:a', 'copy',
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
            
            return video_path
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing subtitles (drawtext): {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process subtitles with drawtext: {e}") from e

