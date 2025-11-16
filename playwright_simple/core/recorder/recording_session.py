#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recording Session.

Manages write mode operations: event capture, conversion, and YAML writing.
"""

import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from .event_capture import EventCapture
from .action_converter import ActionConverter
from .yaml_writer import YAMLWriter
from .event_handlers import EventHandlers
from .recorder_logger import RecorderLogger
from .exceptions import RecordingSessionError
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class RecordingSession:
    """Manages recording session (write mode)."""
    
    __slots__ = (
        'page', 'yaml_writer', 'action_converter', 'event_handlers',
        'recorder_logger', 'debug', 'event_capture', 'is_recording', 'is_paused'
    )
    
    def __init__(
        self,
        page: Page,
        yaml_writer: YAMLWriter,
        action_converter: ActionConverter,
        event_handlers: EventHandlers,
        recorder_logger: Optional[RecorderLogger] = None,
        debug: bool = False
    ) -> None:
        """
        Initialize recording session.
        
        Args:
            page: Playwright Page instance
            yaml_writer: YAMLWriter instance
            action_converter: ActionConverter instance
            event_handlers: EventHandlers instance
            recorder_logger: Optional RecorderLogger instance
            debug: Enable debug mode
        
        Raises:
            RecordingSessionError: If required dependencies are invalid
        """
        # Validate required dependencies
        if page is None:
            raise RecordingSessionError(
                "Page instance is required",
                details={'parameter': 'page'}
            )
        if yaml_writer is None:
            raise RecordingSessionError(
                "YAMLWriter instance is required",
                details={'parameter': 'yaml_writer'}
            )
        if action_converter is None:
            raise RecordingSessionError(
                "ActionConverter instance is required",
                details={'parameter': 'action_converter'}
            )
        if event_handlers is None:
            raise RecordingSessionError(
                "EventHandlers instance is required",
                details={'parameter': 'event_handlers'}
            )
        self.page = page
        self.yaml_writer = yaml_writer
        self.action_converter = action_converter
        self.event_handlers = event_handlers
        self.recorder_logger = recorder_logger
        self.debug = debug
        
        self.event_capture: Optional[EventCapture] = None
        self.is_recording = False
        self.is_paused = False
    
    async def start(self) -> None:
        """Start recording session."""
        # Initialize event capture
        self.event_capture = EventCapture(
            self.page,
            debug=self.debug,
            event_handlers_instance=self.event_handlers,
            recorder_logger=self.recorder_logger
        )
        
        # Log event capture initialized
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='event_capture_initialized',
                page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                details={'debug': self.debug}
            )
        
        # Start event capture
        await self.event_capture.start()
        
        # Log event capture started
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='event_capture_started',
                page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'}
            )
        
        self.is_recording = True
    
    async def stop(self) -> None:
        """Stop recording session."""
        if self.event_capture:
            await self.event_capture.stop()
            self.event_capture = None
        
        self.is_recording = False
    
    def set_recording_state(self, is_recording: bool) -> None:
        """Set recording state."""
        self.is_recording = is_recording
    
    def set_paused_state(self, is_paused: bool) -> None:
        """Set paused state."""
        self.is_paused = is_paused

