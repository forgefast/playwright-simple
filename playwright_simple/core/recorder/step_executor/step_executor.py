#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step executor for YAML steps.

Handles execution of individual steps with audio synchronization.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ...step import TestStep
from .action_executors import ActionExecutors

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes YAML steps with audio synchronization."""
    
    def __init__(
        self,
        page,
        command_handlers,
        recorder_logger=None,
        speed_level=None,
        video_start_time=None,
        wait_for_page_stable=None,
        play_audio_for_step=None,
        estimate_audio_duration=None,
        pre_generated_audio_info=None
    ):
        """
        Initialize step executor.
        
        Args:
            page: Playwright page object
            command_handlers: Command handlers instance
            recorder_logger: Optional recorder logger
            speed_level: Optional speed level configuration
            video_start_time: Video recording start time
            wait_for_page_stable: Function to wait for page to stabilize
            play_audio_for_step: Function to play audio for a step
            estimate_audio_duration: Function to estimate audio duration
            pre_generated_audio_info: Dict with pre-generated audio info from TTSManager.pre_generate_audios()
        """
        self.page = page
        self.command_handlers = command_handlers
        self.recorder_logger = recorder_logger
        self.speed_level = speed_level
        self.video_start_time = video_start_time or datetime.now()
        self._wait_for_page_stable = wait_for_page_stable
        self._play_audio_for_step = play_audio_for_step
        self._estimate_audio_duration = estimate_audio_duration
        self.pre_generated_audio_info = pre_generated_audio_info or {}
        
        # Initialize action executors
        self.action_executors = ActionExecutors(
            page=page,
            command_handlers=command_handlers,
            recorder_logger=recorder_logger,
            speed_level=speed_level,
            wait_for_page_stable=wait_for_page_stable
        )
        
        self.steps: List[TestStep] = []
        self.last_audio_end_time = 0.0  # Track when last audio ended (relative to video start)
    
    async def execute_steps(self, yaml_steps: List[Dict[str, Any]]) -> List[TestStep]:
        """
        Execute YAML steps with audio synchronization.
        
        Args:
            yaml_steps: List of step dictionaries from YAML
            
        Returns:
            List of TestStep objects with all timing and content data
        """
        if not yaml_steps:
            logger.warning("No YAML steps to execute")
            return []
        
        video_start_datetime = self.video_start_time
        current_subtitle = None
        current_audio = None
        last_audio_task = None
        
        # Extract pre-generated audio info
        audio_data = self.pre_generated_audio_info.get('audio_data', {})
        adjusted_timestamps = self.pre_generated_audio_info.get('adjusted_timestamps', {})
        audio_end_times = self.pre_generated_audio_info.get('audio_end_times', {})
        
        # Log execution start
        if self.recorder_logger:
            total_steps = len(yaml_steps)
            try:
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            page_url = self.page.url if hasattr(self.page, 'url') else 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_started',
                page_state={'url': page_url, 'title': page_title},
                details={'total_steps': total_steps}
            )
        
        for i, step in enumerate(yaml_steps, 1):
            action = step.get('action')
            description = step.get('description', '')
            subtitle = step.get('subtitle')
            audio = step.get('audio')
            
            step_start_datetime = datetime.now()
            step_start_elapsed = (step_start_datetime - video_start_datetime).total_seconds()
            
            # Set step context
            if self.recorder_logger:
                self.recorder_logger.set_step_context(i, action)
            
            # Log step execution start
            if self.recorder_logger:
                try:
                    if hasattr(self.page, 'title'):
                        page_title = await self.page.title()
                    else:
                        page_title = 'N/A'
                except:
                    page_title = 'N/A'
                page_state = {
                    'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                    'title': page_title
                }
                self.recorder_logger.set_page_state(page_state)
            
            # Handle subtitle continuity
            if subtitle is not None:
                if subtitle == '':
                    current_subtitle = None
                else:
                    current_subtitle = subtitle
            elif current_subtitle:
                pass  # Continue previous subtitle
            
            # Handle audio continuity
            if audio is not None:
                if audio == '':
                    current_audio = None
                else:
                    current_audio = audio
            elif current_audio:
                pass  # Continue previous audio
            
            # Create TestStep object
            test_step = TestStep(
                step_number=i,
                action=step,
                subtitle=current_subtitle,
                description=description,
                video_start_time=video_start_datetime,
                audio=current_audio
            )
            
            # AUDIO SYNCHRONIZATION: Wait for previous audio to finish if this step has audio
            # This ensures video is recorded with correct timestamps from the start
            if i in audio_data and i in adjusted_timestamps and i in audio_end_times:
                # Step has pre-generated audio
                current_time_elapsed = step_start_elapsed
                
                # Check if previous step has audio that is still playing
                previous_audio_end_time = None
                if i > 1 and (i - 1) in audio_end_times:
                    # Previous step has audio - check when it ends
                    previous_audio_end_time = audio_end_times[i - 1]
                
                # Determine when this step should start
                # If previous audio is still playing, wait until it finishes
                if previous_audio_end_time is not None and previous_audio_end_time > current_time_elapsed:
                    # Previous audio is still playing - wait until it finishes
                    wait_time = previous_audio_end_time - current_time_elapsed
                    logger.info(f"🎤 Step {i}: Waiting {wait_time:.2f}s for previous audio to finish (previous audio ends at {previous_audio_end_time:.2f}s, current time: {current_time_elapsed:.2f}s)")
                    await asyncio.sleep(wait_time)
                    # Update step start time after waiting
                    step_start_datetime = datetime.now()
                    step_start_elapsed = (step_start_datetime - video_start_datetime).total_seconds()
                    logger.info(f"🎤 Step {i}: Waited, new start time: {step_start_elapsed:.2f}s")
                else:
                    # No previous audio or it already finished - use adjusted timestamp if available
                    adjusted_start_time = adjusted_timestamps[i]
                    if adjusted_start_time > current_time_elapsed:
                        wait_time = adjusted_start_time - current_time_elapsed
                        logger.info(f"🎤 Step {i}: Waiting {wait_time:.2f}s to reach adjusted start time (should start at {adjusted_start_time:.2f}s, current time: {current_time_elapsed:.2f}s)")
                        await asyncio.sleep(wait_time)
                        step_start_datetime = datetime.now()
                        step_start_elapsed = (step_start_datetime - video_start_datetime).total_seconds()
                        logger.info(f"🎤 Step {i}: Waited, new start time: {step_start_elapsed:.2f}s")
                
                # Store audio data in step
                audio_file, audio_duration = audio_data[i]
                test_step.audio_file_path = audio_file
                test_step.audio_duration_seconds = audio_duration
                
                # Update last_audio_end_time to when THIS audio ends
                # audio_end_times[i] is when this audio ends (relative to video start)
                self.last_audio_end_time = audio_end_times[i]
            
            # Initialize timing - mark as starting
            test_step.start()
            test_step._start_seconds = step_start_elapsed
            test_step.start_time = step_start_datetime
            
            # Start timer
            step_action_id = f"step_{i}_{action}"
            if self.recorder_logger:
                self.recorder_logger.start_action_timer(step_action_id)
            
            try:
                # Mark as executing
                test_step.execute()
                test_step.execute_time = datetime.now()
                
                # Execute action using action executors
                if action == 'go_to':
                    await self.action_executors.execute_go_to(step, i)
                elif action == 'click':
                    await self.action_executors.execute_click(step, i)
                elif action == 'type':
                    await self.action_executors.execute_type(step, i)
                elif action == 'submit':
                    await self.action_executors.execute_submit(step, i)
                elif action == 'wait':
                    await self.action_executors.execute_wait(step, i)
                
                # Mark as waiting for load
                test_step.wait_load()
                test_step.wait_load_time = datetime.now()
                
            except Exception as e:
                step_error_datetime = datetime.now()
                step_error_elapsed = (step_error_datetime - video_start_datetime).total_seconds()
                
                if self.recorder_logger:
                    duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                    page_state = {
                        'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                        'title': await self.page.title() if hasattr(self.page, 'title') else 'N/A'
                    }
                    self.recorder_logger.log_critical_failure(
                        action=f'step_{i}_{action}',
                        error=str(e),
                        page_state=page_state
                    )
                    self.recorder_logger.log_step_execution(
                        step_number=i,
                        action=action,
                        success=False,
                        duration_ms=duration_ms,
                        error=str(e),
                        page_state=page_state
                    )
                
                # Mark step as failed
                test_step.fail_with_error(e)
                test_step._end_seconds = step_error_elapsed
                test_step._duration = step_error_elapsed - test_step._start_seconds
                self.steps.append(test_step)
                raise
            
            # Calculate step end time (based on actual execution, not audio playback)
            step_end_datetime = datetime.now()
            step_end_elapsed = (step_end_datetime - video_start_datetime).total_seconds()
            step_duration = step_end_elapsed - test_step._start_seconds
            
            # Mark as completed
            test_step.complete()
            test_step._end_seconds = step_end_elapsed
            test_step._duration = step_duration
            
            self.steps.append(test_step)
        
        # Log execution completed
        if self.recorder_logger:
            try:
                page_url = self.page.url if hasattr(self.page, 'url') else 'N/A'
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_completed',
                page_state={'url': page_url, 'title': page_title},
                details={'total_steps': len(yaml_steps)}
            )
        
        return self.steps

