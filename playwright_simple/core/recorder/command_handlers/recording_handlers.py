#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recording Control Handlers.

Handles recording control commands (start, save, exit, pause, resume).
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RecordingHandlers:
    """Handles recording control commands."""
    
    def __init__(
        self,
        yaml_writer,
        event_capture_getter: Callable,
        recording_state_setter: Callable,
        paused_state_setter: Callable
    ):
        """Initialize recording handlers."""
        self.yaml_writer = yaml_writer
        self._get_event_capture = event_capture_getter
        self._set_recording = recording_state_setter
        self._set_paused = paused_state_setter
    
    async def handle_start(self, args: str, is_recording: bool) -> None:
        """Handle start command."""
        if is_recording:
            print("⚠️  Already recording")
            return
        
        self._set_paused(False)
        self._set_recording(True)
        event_capture = self._get_event_capture()
        if event_capture:
            await event_capture.start()
        print("✅ Recording started")
    
    async def handle_save(self, args: str) -> None:
        """Handle save command - save YAML without stopping."""
        logger.info("Save command handler called")
        steps_count = self.yaml_writer.get_steps_count()
        
        if steps_count > 0:
            logger.info(f"Saving YAML (continuing recording)... Total steps: {steps_count}")
            success = self.yaml_writer.save()
            if success:
                saved_path = self.yaml_writer.output_path.resolve()
                logger.info(f"✅ YAML saved successfully to: {saved_path}")
                print(f"\n💾 YAML saved! (continuing recording)")
                print(f"   File: {saved_path}")
                print(f"   Steps saved: {steps_count}")
                print(f"   Continue interacting...\n")
            else:
                logger.error(f"❌ Failed to save YAML")
                print(f"\n❌ Failed to save YAML")
                print(f"   Check log file for details\n")
        else:
            logger.warning("No steps to save yet")
            print(f"\n⚠️  No steps recorded yet")
            print(f"   Continue interacting and try again\n")
    
    async def handle_exit(self, args: str) -> None:
        """Handle exit command - exit without saving."""
        logger.info("Exit command handler called")
        print("🚪 Exiting without saving...")
        logger.info("Exit command handler completed (stop(save=False) will be called from _wait_for_exit)")
    
    async def handle_pause(self, args: str) -> None:
        """Handle pause command."""
        self._set_paused(True)
        print("⏸️  Recording paused")
    
    async def handle_resume(self, args: str) -> None:
        """Handle resume command."""
        self._set_paused(False)
        print("▶️  Recording resumed")

