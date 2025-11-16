#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager.

Factory for creating appropriate session types (Recording or Playback).
"""

import logging
from typing import Optional, Union
from pathlib import Path
from datetime import datetime

from .recording_session import RecordingSession
from .playback_session import PlaybackSession
from .yaml_writer import YAMLWriter
from .action_converter import ActionConverter
from .event_handlers import EventHandlers
from .command_handlers import CommandHandlers
from .recorder_logger import RecorderLogger
from .config import RecorderConfig
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session creation and lifecycle."""
    
    def __init__(
        self,
        config: RecorderConfig,
        page: Page,
        yaml_writer: Optional[YAMLWriter],
        action_converter: ActionConverter,
        event_handlers: EventHandlers,
        command_handlers: CommandHandlers,
        recorder_logger: Optional[RecorderLogger] = None,
        yaml_steps: Optional[list] = None,
        yaml_data: Optional[dict] = None,
        video_start_time: Optional[datetime] = None
    ):
        """
        Initialize session manager.
        
        Args:
            config: RecorderConfig instance
            page: Playwright Page instance
            yaml_writer: YAMLWriter instance (for write mode)
            action_converter: ActionConverter instance
            event_handlers: EventHandlers instance
            command_handlers: CommandHandlers instance
            recorder_logger: Optional RecorderLogger instance
            yaml_steps: List of YAML steps (for read mode)
            yaml_data: Full YAML data (for read mode)
            video_start_time: Video start time (for read mode)
        """
        self.config = config
        self.page = page
        self.yaml_writer = yaml_writer
        self.action_converter = action_converter
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.recorder_logger = recorder_logger
        self.yaml_steps = yaml_steps
        self.yaml_data = yaml_data
        self.video_start_time = video_start_time
        
        self.session: Optional[RecordingSession | PlaybackSession] = None
    
    def create_session(self) -> RecordingSession | PlaybackSession:
        """
        Create appropriate session based on mode.
        
        Returns:
            RecordingSession or PlaybackSession instance
        """
        if self.config.mode == 'write':
            if not self.yaml_writer:
                raise ValueError("YAMLWriter required for write mode")
            
            self.session = RecordingSession(
                page=self.page,
                yaml_writer=self.yaml_writer,
                action_converter=self.action_converter,
                event_handlers=self.event_handlers,
                recorder_logger=self.recorder_logger,
                debug=self.config.debug
            )
        else:  # read mode
            if not self.yaml_steps:
                raise ValueError("YAML steps required for read mode")
            
            self.session = PlaybackSession(
                page=self.page,
                yaml_steps=self.yaml_steps,
                yaml_data=self.yaml_data or {},
                command_handlers=self.command_handlers,
                recorder_logger=self.recorder_logger,
                fast_mode=self.config.fast_mode,
                video_start_time=self.video_start_time
            )
        
        return self.session
    
    async def start(self):
        """Start the session."""
        if not self.session:
            self.create_session()
        
        if isinstance(self.session, RecordingSession):
            await self.session.start()
        elif isinstance(self.session, PlaybackSession):
            await self.session.execute()
    
    async def stop(self):
        """Stop the session."""
        if isinstance(self.session, RecordingSession):
            await self.session.stop()

