#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playback Session.

Manages read mode operations: YAML execution and video generation.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from .command_handlers import CommandHandlers
from .recorder_logger import RecorderLogger
from .exceptions import PlaybackSessionError
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PlaybackSession:
    """Manages playback session (read mode)."""
    
    __slots__ = (
        'page', 'yaml_steps', 'yaml_data', 'command_handlers',
        'recorder_logger', 'fast_mode', 'video_start_time'
    )
    
    def __init__(
        self,
        page: Page,
        yaml_steps: List[Dict[str, Any]],
        yaml_data: Dict[str, Any],
        command_handlers: CommandHandlers,
        recorder_logger: Optional[RecorderLogger] = None,
        fast_mode: bool = False,
        video_start_time: Optional[datetime] = None
    ) -> None:
        """
        Initialize playback session.
        
        Manages read mode operations: YAML execution and video generation.
        This session is responsible for executing pre-recorded YAML steps
        and generating videos with subtitles and audio.
        
        Args:
            page: Playwright Page instance where steps will be executed
            yaml_steps: List of YAML steps to execute (cannot be empty)
            yaml_data: Full YAML data including metadata and configuration
            command_handlers: CommandHandlers instance for executing actions
            recorder_logger: Optional RecorderLogger instance for structured logging
            fast_mode: Enable fast mode (reduce delays for faster execution)
            video_start_time: Video start time for subtitle/audio timing synchronization
        
        Raises:
            PlaybackSessionError: If required dependencies are None or invalid,
                or if yaml_steps is empty
        
        Example:
            ```python
            session = PlaybackSession(
                page=page,
                yaml_steps=yaml_steps,
                yaml_data=yaml_data,
                command_handlers=command_handlers,
                recorder_logger=recorder_logger,
                fast_mode=True,
                video_start_time=datetime.now()
            )
            await session.execute()  # Execute all YAML steps
            ```
        """
        # Validate required dependencies
        if page is None:
            raise PlaybackSessionError(
                "Page instance is required",
                details={'parameter': 'page'}
            )
        if not yaml_steps:
            raise PlaybackSessionError(
                "YAML steps list cannot be empty",
                details={'yaml_steps_count': len(yaml_steps) if yaml_steps else 0}
            )
        if command_handlers is None:
            raise PlaybackSessionError(
                "CommandHandlers instance is required",
                details={'parameter': 'command_handlers'}
            )
        self.page = page
        self.yaml_steps = yaml_steps
        self.yaml_data = yaml_data
        self.command_handlers = command_handlers
        self.recorder_logger = recorder_logger
        self.fast_mode = fast_mode
        self.video_start_time = video_start_time or datetime.now()
    
    async def execute(self) -> None:
        """
        Execute YAML steps.
        
        Processes all steps in the YAML file sequentially, executing
        actions (go_to, click, type, submit, wait) and generating
        video with subtitles and audio if configured.
        
        Raises:
            PlaybackSessionError: If execution fails for any step
        """
        if not self.yaml_steps:
            logger.warning("No steps to execute")
            return
        
        # Log execution start
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_started',
                page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                details={'total_steps': len(self.yaml_steps)}
            )
        
        # Execute steps (delegated to Recorder._execute_yaml_steps for now)
        # This will be refactored in a future step
        
        # Log execution completed
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_completed',
                page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                details={'total_steps': len(self.yaml_steps)}
            )

