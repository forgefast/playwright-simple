#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event handlers for recorder.

Handles conversion of browser events to YAML steps.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventHandlers:
    """Handles browser events during recording."""
    
    def __init__(self, action_converter, yaml_writer, is_recording_getter, is_paused_getter):
        """
        Initialize event handlers.
        
        Args:
            action_converter: ActionConverter instance
            yaml_writer: YAMLWriter instance
            is_recording_getter: Callable that returns recording state
            is_paused_getter: Callable that returns paused state
        """
        self.action_converter = action_converter
        self.yaml_writer = yaml_writer
        self._is_recording = is_recording_getter
        self._is_paused = is_paused_getter
    
    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._is_recording()
    
    @property
    def is_paused(self) -> bool:
        """Check if recording is paused."""
        return self._is_paused()
    
    def handle_click(self, event_data: dict) -> None:
        """Handle click event."""
        if not self.is_recording or self.is_paused:
            logger.debug("Click ignored: not recording or paused")
            return
        
        logger.debug(f"Processing click event: {event_data}")
        try:
            action = self.action_converter.convert_click(event_data)
            if action:
                # CRITICAL: Add step immediately, before any navigation can happen
                self.yaml_writer.add_step(action)
                logger.info(f"Added click step: {action.get('description', '')}")
                print(f"📝 Click: {action.get('description', '')}")
            else:
                logger.error(f"❌ Click event not converted to action! Event data: {event_data}")
                print(f"❌ ERRO: Click não foi convertido em ação! {event_data.get('element', {}).get('tagName', 'unknown')}")
        except Exception as e:
            logger.error(f"Error handling click event: {e}", exc_info=True)
            print(f"❌ ERRO ao processar click: {e}")
    
    def handle_input(self, event_data: dict) -> None:
        """Handle input event - accumulates, doesn't save yet."""
        if not self.is_recording or self.is_paused:
            logger.debug("Input ignored: not recording or paused")
            return
        
        logger.debug(f"Processing input event (accumulating): {event_data}")
        # convert_input now accumulates and returns None
        self.action_converter.convert_input(event_data)
        # Action will be created on blur or Enter
    
    def handle_blur(self, event_data: dict) -> None:
        """Handle blur event - finalize input."""
        if not self.is_recording or self.is_paused:
            return
        
        logger.debug(f"Processing blur event: {event_data}")
        element_info = event_data.get('element', {})
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_type = element_info.get('type', '')
        element_key = f"{element_id}:{element_name}:{element_type}"
        
        action = self.action_converter.finalize_input(element_key)
        if action:
            self.yaml_writer.add_step(action)
            value_preview = action.get('text', '')[:50]
            if len(action.get('text', '')) > 50:
                value_preview += '...'
            logger.info(f"Finalized input on blur: {action.get('description', '')} = '{value_preview}'")
            print(f"📝 Type: {action.get('description', '')} = '{value_preview}'")
    
    def handle_navigation(self, event_data: dict) -> None:
        """Handle navigation event."""
        if not self.is_recording or self.is_paused:
            return
        
        url = event_data.get('url', '')
        previous_url = event_data.get('previous_url', '')
        
        # Skip if it's the initial URL (already added)
        if url == self.action_converter.initial_url:
            logger.debug(f"Skipping navigation to initial URL: {url}")
            return
        
        # CRITICAL: Clear all pending inputs on navigation
        # Events from the previous page should NOT be finalized after navigation
        # This prevents capturing input events that happened before navigation
        if self.action_converter.pending_inputs:
            logger.debug(f"Clearing {len(self.action_converter.pending_inputs)} pending input(s) on navigation (from previous page)")
            self.action_converter.pending_inputs.clear()
        
        # Skip all navigations - they're caused by clicks which are already captured as 'click' actions
        # Only the initial URL is recorded (done in start())
        logger.debug(f"Skipping navigation from {previous_url} to {url} (click already captured)")
    
    def handle_scroll(self, event_data: dict) -> None:
        """Handle scroll event."""
        if not self.is_recording or self.is_paused:
            return
        
        action = self.action_converter.convert_scroll(event_data)
        if action:
            self.yaml_writer.add_step(action)
            print(f"📝 Scroll: {action.get('description', '')}")

