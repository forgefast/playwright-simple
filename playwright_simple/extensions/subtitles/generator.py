#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle generator for subtitles extension.

Moved from core/runner/subtitle_generator.py to keep core minimal.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime

from .config import SubtitleConfig
from ...extensions.video.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Handles subtitle generation and embedding."""
    
    def __init__(self, config: SubtitleConfig):
        """
        Initialize subtitle generator.
        
        Args:
            config: Subtitle configuration
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
        if not self.config.enabled:
            return None
        
        if not test_steps:
            return None
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                # Convert TestStep objects to dicts for processing
                step_dicts = []
                for step in test_steps:
                    if hasattr(step, 'to_dict'):
                        step_dicts.append(step.to_dict())
                    elif isinstance(step, dict):
                        step_dicts.append(step)
                    else:
                        logger.warning(f"Unknown step type: {type(step)}, skipping")
                        continue
                
                # Sort steps by start time to ensure proper ordering
                sorted_steps = sorted(step_dicts, key=lambda s: s.get('start_time', 0))
                
                # Process steps and eliminate overlaps
                processed_steps = []
                subtitle_index = 1
                gap = 0.1  # 100ms gap between subtitles to prevent overlap
                min_duration = self.config.min_duration
                
                # First pass: calculate end times for all steps
                for i, step in enumerate(sorted_steps):
                    step_start = step.get('start_time', 0)
                    step_end = step.get('end_time')
                    step_duration = step.get('duration', 0)
                    
                    if step_end is None:
                        step_end = step_start + step_duration
                    
                    step_text = step.get('subtitle') or step.get('text') or step.get('description', f'Passo {subtitle_index}')
                    
                    actual_duration = step_end - step_start
                    if actual_duration < min_duration:
                        step_end = step_start + min_duration
                        actual_duration = min_duration
                    
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'index': subtitle_index,
                        'duration': actual_duration
                    })
                    subtitle_index += 1
                
                # Second pass: adjust end times to prevent overlaps
                max_iterations = 10
                for iteration in range(max_iterations):
                    has_overlaps = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        
                        earliest_next_start = None
                        for j in range(i + 1, len(processed_steps)):
                            next_step_start = processed_steps[j]['start']
                            if next_step_start <= current_step['end']:
                                if earliest_next_start is None or next_step_start < earliest_next_start:
                                    earliest_next_start = next_step_start
                        
                        if earliest_next_start is not None:
                            new_end = earliest_next_start - gap
                            new_end = max(current_step['start'] + 0.1, new_end)
                            if abs(new_end - current_step['end']) > 0.001:
                                current_step['end'] = new_end
                                has_overlaps = True
                    
                    if not has_overlaps:
                        break
                
                # Final pass: ensure no overlaps remain
                for final_iteration in range(10):
                    made_changes = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        for j in range(i + 1, len(processed_steps)):
                            next_step = processed_steps[j]
                            if current_step['end'] >= next_step['start']:
                                new_end = next_step['start'] - gap
                                new_end = max(current_step['start'] + 0.05, new_end)
                                if abs(new_end - current_step['end']) > 0.001:
                                    current_step['end'] = new_end
                                    made_changes = True
                    if not made_changes:
                        break
                
                # Write subtitles
                subtitle_index = 1
                for step in processed_steps:
                    if step['end'] > step['start']:
                        start_time_str = self.format_time(step['start'])
                        end_time_str = self.format_time(step['end'])
                        
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time_str} --> {end_time_str}\n")
                        f.write(f"{step['text']}\n\n")
                        
                        subtitle_index += 1
            
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            return None
    
    async def embed(self, video_path: Path, srt_path: Path) -> Optional[Path]:
        """
        Embed subtitles into video.
        
        Args:
            video_path: Path to video file
            srt_path: Path to SRT file
            
        Returns:
            Path to video with subtitles, or original path if processing failed
        """
        if not self.config.enabled or not self.config.hard_subtitles:
            return video_path
        
        if not srt_path.exists():
            return video_path
        
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found. Cannot embed subtitles.")
            return video_path
        
        output_path = video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}"
        
        try:
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', f"subtitles='{srt_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
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
        except Exception as e:
            logger.error(f"Error embedding subtitles: {e}", exc_info=True)
            return video_path

