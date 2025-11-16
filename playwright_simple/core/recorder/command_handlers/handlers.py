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
        event_capture_getter: Optional[Callable] = None,
        cursor_controller_getter: Optional[Callable] = None,
        recording_state_setter: Optional[Callable] = None,
        paused_state_setter: Optional[Callable] = None,
        page_getter: Optional[Callable] = None,
        recorder = None,
        recorder_logger = None,
        # New: Direct injection (preferred)
        event_capture = None,
        cursor_controller = None,
        page = None
    ):
        """
        Initialize command handlers.
        
        Args:
            yaml_writer: YAMLWriter instance
            event_capture_getter: Callable that returns EventCapture instance (legacy, use event_capture instead)
            cursor_controller_getter: Callable that returns CursorController instance (legacy, use cursor_controller instead)
            recording_state_setter: Callable to set recording state
            paused_state_setter: Callable to set paused state
            page_getter: Optional callable that returns Playwright Page instance (legacy, use page instead)
            recorder: Optional Recorder instance (for accessing action_converter)
            recorder_logger: Optional RecorderLogger instance
            event_capture: Direct EventCapture instance (preferred)
            cursor_controller: Direct CursorController instance (preferred)
            page: Direct Page instance (preferred)
        """
        self.yaml_writer = yaml_writer
        
        # Support both legacy (getters) and new (direct) injection
        use_getters = event_capture_getter is not None or cursor_controller_getter is not None or page_getter is not None
        
        if use_getters:
            # Legacy mode: use getters
            _event_capture_getter = event_capture_getter
            _cursor_controller_getter = cursor_controller_getter
            _page_getter = page_getter
        else:
            # New mode: create getters from direct instances
            _event_capture_getter = lambda: event_capture if event_capture else None
            _cursor_controller_getter = lambda: cursor_controller if cursor_controller else None
            _page_getter = lambda: page if page else None
        
        # Initialize handler modules
        self._recording = RecordingHandlers(
            yaml_writer=yaml_writer,
            event_capture_getter=_event_capture_getter,
            recording_state_setter=recording_state_setter,
            paused_state_setter=paused_state_setter
        )
        
        self._metadata = MetadataHandlers(yaml_writer=yaml_writer)
        
        self._cursor = CursorHandlers(
            yaml_writer=yaml_writer,
            cursor_controller_getter=_cursor_controller_getter
        )
        
        self._playwright = PlaywrightHandlers(
            yaml_writer=yaml_writer,
            page_getter=_page_getter,
            cursor_controller_getter=_cursor_controller_getter,
            recorder=recorder,  # Pass recorder so handlers can access action_converter
            recorder_logger=recorder_logger
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
    
    async def handle_subtitle(self, args: str) -> None:
        """Handle subtitle command."""
        await self._metadata.handle_subtitle(args)
    
    async def handle_audio(self, args: str) -> None:
        """Handle audio command (creates separate step)."""
        await self._metadata.handle_audio(args)
    
    async def handle_audio_step(self, args: str) -> None:
        """Handle audio-step command - adds audio to last step (for narration)."""
        await self._metadata.handle_audio_step(args)
    
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
    
    async def handle_pw_click(self, args: str):
        """Handle pw-click command."""
        return await self._playwright.handle_pw_click(args)
    
    async def handle_pw_type(self, args: str):
        """Handle pw-type command."""
        return await self._playwright.handle_pw_type(args)
    
    async def handle_pw_submit(self, args: str):
        """Handle pw-submit command."""
        return await self._playwright.handle_pw_submit(args)
    
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

