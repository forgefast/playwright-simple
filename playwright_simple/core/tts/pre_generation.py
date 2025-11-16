#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-generation module.

Provides functionality to pre-generate all audio files before step execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .utils import get_audio_duration

logger = logging.getLogger(__name__)


async def pre_generate_audios(
    test_steps: List[Any],  # Can be TestStep objects or dicts
    output_dir: Path,
    test_name: str,
    generate_audio_func  # Function to generate audio: (text, output_path) -> bool
) -> Dict[str, Any]:
    """
    Pre-generate all audio files in parallel and calculate adjusted timestamps.
    
    This function generates all audios BEFORE step execution, allowing the StepExecutor
    to wait for previous audio to finish before executing the next step with audio.
    
    Args:
        test_steps: List of test steps (TestStep objects or dicts)
        output_dir: Directory to save audio files
        test_name: Name of test (for filename)
        generate_audio_func: Async function to generate audio (text, output_path) -> bool
        
    Returns:
        Dictionary with:
            - 'audio_data': Dict mapping step_index -> (audio_file, audio_duration)
            - 'adjusted_timestamps': Dict mapping step_index -> adjusted_start_time
            - 'audio_end_times': Dict mapping step_index -> when audio ends
    """
    if not test_steps:
        return {
            'audio_data': {},
            'adjusted_timestamps': {},
            'audio_end_times': {}
        }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / f"{test_name}_tts_pregen"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        try:
            from ..step import TestStep
        except ImportError:
            TestStep = None
        
        # First pass: prepare all steps with audio text
        # Note: Steps haven't been executed yet, so we use estimated timestamps
        # based on step order. Actual timestamps will be set during execution.
        prepared_steps = []
        current_audio_text = None
        estimated_start_time = 0.0  # Start from 0, will be adjusted during execution
        
        for i, step in enumerate(test_steps, 1):
            if isinstance(step, TestStep):
                step_audio = getattr(step, 'audio', None)
                if step_audio is not None:
                    if step_audio == '':
                        current_audio_text = None
                    else:
                        current_audio_text = step_audio
                step_text = current_audio_text if current_audio_text else None
                # Use estimated duration (will be adjusted based on actual audio durations)
                step_duration = 1.0  # Default estimate, will be adjusted
            elif isinstance(step, dict):
                step_audio = step.get('audio') or step.get('speech')
                if step_audio is not None:
                    if step_audio == '':
                        current_audio_text = None
                    else:
                        current_audio_text = step_audio
                step_text = current_audio_text if current_audio_text else None
                step_duration = step.get('duration', 1.0)  # Use provided or default
            else:
                step_text = current_audio_text if current_audio_text else None
                step_duration = 1.0
            
            prepared_steps.append({
                'step_index': i,
                'audio_text': step_text,
                'estimated_start_time': estimated_start_time,
                'estimated_duration': step_duration,
                'original_step': step
            })
            
            # Estimate next step start (will be adjusted based on audio durations)
            estimated_start_time += step_duration
        
        # Second pass: group consecutive steps with same audio text
        audio_groups = []
        current_group = None
        for step_data in prepared_steps:
            audio_text = step_data['audio_text']
            estimated_start = step_data['estimated_start_time']
            estimated_duration = step_data['estimated_duration']
            
            if audio_text and audio_text.strip():
                if current_group and current_group['audio_text'] == audio_text:
                    current_group['estimated_duration'] += estimated_duration
                    current_group['estimated_end_time'] = estimated_start + estimated_duration
                    current_group['step_indices'].append(step_data['step_index'])
                else:
                    if current_group:
                        audio_groups.append(current_group)
                    current_group = {
                        'audio_text': audio_text,
                        'estimated_start_time': estimated_start,
                        'estimated_duration': estimated_duration,
                        'estimated_end_time': estimated_start + estimated_duration,
                        'step_indices': [step_data['step_index']]
                    }
            else:
                if current_group:
                    audio_groups.append(current_group)
                    current_group = None
        
        if current_group:
            audio_groups.append(current_group)
        
        # Third pass: generate ALL audio files in parallel
        logger.info(f"🎵 Pre-generating {len([g for g in audio_groups if g.get('audio_text')])} audio files in parallel...")
        
        async def generate_group_audio(group_idx: int, group: Dict[str, Any]) -> Tuple[int, Optional[Path], Optional[float], bool]:
            """Generate audio for a single group"""
            if group['audio_text'] and group['audio_text'].strip():
                audio_file = temp_dir / f"group_{group_idx}.mp3"
                try:
                    success = await generate_audio_func(group['audio_text'], audio_file)
                    if success and audio_file.exists():
                        audio_duration = get_audio_duration(audio_file)
                        return (group_idx, audio_file, audio_duration, True)
                    else:
                        return (group_idx, None, None, False)
                except Exception as e:
                    logger.error(f"TTS generation error for group {group_idx}: {e}")
                    return (group_idx, None, None, False)
            else:
                return (group_idx, None, None, False)
        
        # Generate all audio files in parallel
        audio_generation_tasks = []
        for group_idx, group in enumerate(audio_groups, 1):
            if group.get('audio_text') and group['audio_text'].strip():
                audio_generation_tasks.append(generate_group_audio(group_idx, group))
        
        audio_results = await asyncio.gather(*audio_generation_tasks, return_exceptions=True)
        
        # Store results
        audio_results_dict = {}
        for result in audio_results:
            if isinstance(result, Exception):
                logger.error(f"Error generating audio: {result}")
                continue
            group_idx, audio_file, audio_duration, success = result
            if success and audio_file:
                audio_results_dict[group_idx] = (audio_file, audio_duration)
        
        # Fourth pass: map audio data to steps and calculate adjusted timestamps
        # This calculates when each step SHOULD start based on real audio durations
        audio_data = {}  # step_index -> (audio_file, audio_duration)
        adjusted_timestamps = {}  # step_index -> adjusted_start_time (relative to video start)
        audio_end_times = {}  # step_index -> when audio ends (relative to video start)
        
        last_audio_end_time = 0.0
        
        for group_idx, group in enumerate(audio_groups, 1):
            if group['audio_text'] and group['audio_text'].strip():
                if group_idx in audio_results_dict:
                    audio_file, audio_duration = audio_results_dict[group_idx]
                    estimated_start = group['estimated_start_time']
                    
                    # Calculate when this audio should actually start
                    # If previous audio extends beyond estimated start, wait for it
                    if last_audio_end_time > estimated_start:
                        adjusted_start = last_audio_end_time
                        logger.info(f"🎵 Audio group {group_idx}: estimated start {estimated_start:.2f}s, adjusted to {adjusted_start:.2f}s (previous audio ends at {last_audio_end_time:.2f}s)")
                    else:
                        adjusted_start = estimated_start
                    
                    audio_end = adjusted_start + audio_duration
                    
                    # Store for all steps in this group
                    for step_idx in group['step_indices']:
                        audio_data[step_idx] = (audio_file, audio_duration)
                        adjusted_timestamps[step_idx] = adjusted_start
                        audio_end_times[step_idx] = audio_end
                    
                    last_audio_end_time = audio_end
                else:
                    # Failed to generate audio - use estimated timestamps
                    for step_idx in group['step_indices']:
                        adjusted_timestamps[step_idx] = group['estimated_start_time']
                        audio_end_times[step_idx] = group['estimated_start_time']
        
        # Fill in steps without audio (they don't affect audio timing)
        for step_data in prepared_steps:
            step_idx = step_data['step_index']
            if step_idx not in adjusted_timestamps:
                adjusted_timestamps[step_idx] = step_data['estimated_start_time']
                audio_end_times[step_idx] = step_data['estimated_start_time']
        
        logger.info(f"🎵 Pre-generated {len(audio_data)} audio files with adjusted timestamps")
        
        return {
            'audio_data': audio_data,
            'adjusted_timestamps': adjusted_timestamps,
            'audio_end_times': audio_end_times,
            'temp_dir': temp_dir
        }
        
    except Exception as e:
        logger.error(f"Error in pre_generate_audios: {e}", exc_info=True)
        return {
            'audio_data': {},
            'adjusted_timestamps': {},
            'audio_end_times': {}
        }

