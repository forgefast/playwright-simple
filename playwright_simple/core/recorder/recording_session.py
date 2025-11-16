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
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class RecordingSession:
    """Manages recording session (write mode)."""
    
    def __init__(
        self,
        page: Page,
        yaml_writer: YAMLWriter,
        action_converter: ActionConverter,
        event_handlers: EventHandlers,
        recorder_logger: Optional[RecorderLogger] = None,
        debug: bool = False
    ):
        """
        Initialize recording session.
        
        Args:
            page: Playwright Page instance
            yaml_writer: YAMLWriter instance
            action_converter: ActionConverter instance
            event_handlers: EventHandlers instance
            recorder_logger: Optional RecorderLogger instance
            debug: Enable debug mode
        """
        self.page = page
        self.yaml_writer = yaml_writer
        self.action_converter = action_converter
        self.event_handlers = event_handlers
        self.recorder_logger = recorder_logger
        self.debug = debug
        
        self.event_capture: Optional[EventCapture] = None
        self.is_recording = False
        self.is_paused = False
    
    async def start(self):
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
    
    async def stop(self):
        """Stop recording session."""
        if self.event_capture:
            await self.event_capture.stop()
            self.event_capture = None
        
        self.is_recording = False
    
    def set_recording_state(self, is_recording: bool):
        """Set recording state."""
        self.is_recording = is_recording
    
    def set_paused_state(self, is_paused: bool):
        """Set paused state."""
        self.is_paused = is_paused

