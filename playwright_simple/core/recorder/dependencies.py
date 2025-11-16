#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder Dependencies.

Container for recorder dependencies to enable explicit dependency injection.
"""

from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path

from playwright.async_api import Page
from .yaml_writer import YAMLWriter
from .event_capture import EventCapture
from .cursor_controller import CursorController
from .recorder_logger import RecorderLogger


@dataclass
class RecorderDependencies:
    """
    Container for recorder dependencies.
    
    Provides explicit dependency injection instead of using lambdas/getters.
    """
    
    # Core dependencies
    yaml_writer: Optional[YAMLWriter] = None
    event_capture: Optional[EventCapture] = None
    cursor_controller: Optional[CursorController] = None
    page: Optional[Page] = None
    recorder_logger: Optional[RecorderLogger] = None
    
    # State management (callbacks for setting state)
    recording_state_setter: Optional[Callable[[bool], None]] = None
    paused_state_setter: Optional[Callable[[bool], None]] = None
    
    # Recorder instance (for accessing action_converter and other methods)
    recorder: Optional[object] = None
    
    def get_event_capture(self) -> Optional[EventCapture]:
        """Get event capture instance."""
        return self.event_capture
    
    def get_cursor_controller(self) -> Optional[CursorController]:
        """Get cursor controller instance."""
        return self.cursor_controller
    
    def get_page(self) -> Optional[Page]:
        """Get page instance."""
        return self.page
    
    def set_recording_state(self, value: bool) -> None:
        """Set recording state."""
        if self.recording_state_setter:
            self.recording_state_setter(value)
    
    def set_paused_state(self, value: bool) -> None:
        """Set paused state."""
        if self.paused_state_setter:
            self.paused_state_setter(value)

