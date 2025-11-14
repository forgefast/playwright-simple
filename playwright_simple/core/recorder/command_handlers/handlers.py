#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main CommandHandlers class.

Coordinates all handler modules.
"""

from typing import Optional, Callable

from .recording_handlers import RecordingHandlers
from .metadata_handlers import MetadataHandlers
from .cursor_handlers import CursorHandlers
from .playwright_handlers import PlaywrightHandlers


class CommandHandlers:
    """Handles console commands during recording."""
    
    def __init__(
        self,
        yaml_writer,
        event_capture_getter: Callable,
        cursor_controller_getter: Callable,
        recording_state_setter: Callable,
        paused_state_setter: Callable,
        page_getter: Optional[Callable] = None,
        recorder = None
    ):
        """
        Initialize command handlers.
        
        Args:
            yaml_writer: YAMLWriter instance
            event_capture_getter: Callable that returns EventCapture instance
            cursor_controller_getter: Callable that returns CursorController instance
            recording_state_setter: Callable to set recording state
            paused_state_setter: Callable to set paused state
            page_getter: Optional callable that returns Playwright Page instance
            recorder: Optional Recorder instance (for accessing action_converter)
        """
        self.yaml_writer = yaml_writer
        
        # Initialize handler modules
        self._recording = RecordingHandlers(
            yaml_writer=yaml_writer,
            event_capture_getter=event_capture_getter,
            recording_state_setter=recording_state_setter,
            paused_state_setter=paused_state_setter
        )
        
        self._metadata = MetadataHandlers(yaml_writer=yaml_writer)
        
        self._cursor = CursorHandlers(
            yaml_writer=yaml_writer,
            cursor_controller_getter=cursor_controller_getter
        )
        
        self._playwright = PlaywrightHandlers(
            yaml_writer=yaml_writer,
            page_getter=page_getter,
            cursor_controller_getter=cursor_controller_getter,
            recorder=recorder  # Pass recorder so handlers can access action_converter
        )
    
    # Recording control
    async def handle_start(self, args: str, is_recording: bool) -> None:
        """Handle start command."""
        await self._recording.handle_start(args, is_recording)
    
    async def handle_save(self, args: str) -> None:
        """Handle save command."""
        await self._recording.handle_save(args)
    
    async def handle_exit(self, args: str) -> None:
        """Handle exit command."""
        await self._recording.handle_exit(args)
    
    async def handle_pause(self, args: str) -> None:
        """Handle pause command."""
        await self._recording.handle_pause(args)
    
    async def handle_resume(self, args: str) -> None:
        """Handle resume command."""
        await self._recording.handle_resume(args)
    
    # Metadata
    async def handle_caption(self, args: str) -> None:
        """Handle caption command."""
        await self._metadata.handle_caption(args)
    
    async def handle_audio(self, args: str) -> None:
        """Handle audio command."""
        await self._metadata.handle_audio(args)
    
    async def handle_screenshot(self, args: str) -> None:
        """Handle screenshot command."""
        await self._metadata.handle_screenshot(args)
    
    # Cursor
    async def handle_cursor(self, args: str) -> None:
        """Handle cursor command."""
        await self._cursor.handle_cursor(args)
    
    async def handle_cursor_click(self, args: str) -> None:
        """Handle click command."""
        await self._cursor.handle_cursor_click(args)
    
    async def handle_type(self, args: str) -> None:
        """Handle type command."""
        await self._cursor.handle_type(args)
    
    async def handle_press(self, args: str) -> None:
        """Handle press command."""
        await self._cursor.handle_press(args)
    
    # Playwright direct
    async def handle_find(self, args: str) -> None:
        """Handle find command."""
        await self._playwright.handle_find(args)
    
    async def handle_find_all(self, args: str) -> None:
        """Handle find-all command."""
        await self._playwright.handle_find_all(args)
    
    async def handle_pw_click(self, args: str) -> None:
        """Handle pw-click command."""
        await self._playwright.handle_pw_click(args)
    
    async def handle_pw_type(self, args: str) -> None:
        """Handle pw-type command."""
        await self._playwright.handle_pw_type(args)
    
    async def handle_pw_submit(self, args: str) -> None:
        """Handle pw-submit command."""
        await self._playwright.handle_pw_submit(args)
    
    async def handle_pw_wait(self, args: str) -> None:
        """Handle pw-wait command."""
        await self._playwright.handle_pw_wait(args)
    
    async def handle_pw_info(self, args: str) -> None:
        """Handle pw-info command."""
        await self._playwright.handle_pw_info(args)
    
    async def handle_pw_html(self, args: str) -> None:
        """Handle pw-html command."""
        await self._playwright.handle_pw_html(args)
    
    @property
    def output_path(self):
        """Get output path from yaml_writer."""
        return self.yaml_writer.output_path

