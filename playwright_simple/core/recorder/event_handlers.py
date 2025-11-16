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
    
    def __init__(self, action_converter, yaml_writer, is_recording_getter, is_paused_getter, recorder_logger=None):
        """
        Initialize event handlers.
        
        Args:
            action_converter: ActionConverter instance
            yaml_writer: YAMLWriter instance
            is_recording_getter: Callable that returns recording state
            is_paused_getter: Callable that returns paused state
            recorder_logger: Optional RecorderLogger instance
        """
        self.action_converter = action_converter
        self.yaml_writer = yaml_writer
        self._is_recording = is_recording_getter
        self._is_paused = is_paused_getter
        self.recorder_logger = recorder_logger
    
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
            # Log handler skipped
            if self.recorder_logger and self.recorder_logger.is_debug:
                self.recorder_logger.log_screen_event(
                    event_type='handler_skipped',
                    page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                    details={'handler': 'handle_click', 'reason': 'not_recording' if not self.is_recording else 'paused'}
                )
            return
        
        element_info = event_data.get('element', {})
        element_tag = element_info.get('tagName', 'unknown')
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_text = element_info.get('text', '')
        
        # Build structured element info
        structured_element = {
            'tag': element_tag,
            'id': element_id,
            'name': element_name,
            'text': element_text[:100] if element_text else None
        }
        
        logger.debug(f"Processing click event: {event_data}")
        try:
            action = self.action_converter.convert_click(event_data)
            if action:
                # CRITICAL: Add step immediately, before any navigation can happen
                self.yaml_writer.add_step(action)
                
                # Log with structured logger
                if self.recorder_logger:
                    self.recorder_logger.log_user_action(
                        action_type='click',
                        element_info=structured_element,
                        success=True,
                        details={'action_description': action.get('description', '')}
                    )
                else:
                    logger.info(f"Click action added: {action.get('description', '')}")
            else:
                # Log conversion failure
                if self.recorder_logger:
                    self.recorder_logger.log_user_action(
                        action_type='click',
                        element_info=structured_element,
                        success=False,
                        error="Click event not converted to action"
                    )
                else:
                    logger.error(f"Click event not converted to action! Event data: {event_data}")
        except Exception as e:
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='click',
                    error=str(e),
                    element_info=structured_element
                )
        else:
            logger.error(f"Error handling click event: {e}", exc_info=True)
    
    def handle_input(self, event_data: dict) -> None:
        """Handle input event - accumulates, doesn't save yet."""
        if not self.is_recording or self.is_paused:
            logger.debug("Input ignored: not recording or paused")
            # Log handler skipped
            if self.recorder_logger and self.recorder_logger.is_debug:
                self.recorder_logger.log_screen_event(
                    event_type='handler_skipped',
                    page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                    details={'handler': 'handle_input', 'reason': 'not_recording' if not self.is_recording else 'paused'}
                )
            return
        
        element_info = event_data.get('element', {})
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_type = element_info.get('type', '')
        value = event_data.get('value', '')
        
        logger.debug(f"Processing input event (accumulating): {event_data}")
        # convert_input now accumulates and returns None
        self.action_converter.convert_input(event_data)
        
        # Log with structured logger (debug only)
        if self.recorder_logger and self.recorder_logger.is_debug:
            structured_element = {
                'id': element_id,
                'name': element_name,
                'type': element_type,
                'value_length': len(value)
            }
            self.recorder_logger._log(
                level='DEBUG',
                message=f"Input accumulated for {element_id}:{element_name}:{element_type}",
                action_type='input',
                element_info=structured_element
            )
        # Action will be created on blur or Enter
    
    def handle_blur(self, event_data: dict) -> None:
        """Handle blur event - finalize input."""
        if not self.is_recording or self.is_paused:
            # Log handler skipped
            if self.recorder_logger and self.recorder_logger.is_debug:
                self.recorder_logger.log_screen_event(
                    event_type='handler_skipped',
                    page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                    details={'handler': 'handle_navigation', 'reason': 'not_recording' if not self.is_recording else 'paused'}
                )
            return
        
        logger.debug(f"Processing blur event: {event_data}")
        element_info = event_data.get('element', {})
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_type = element_info.get('type', '')
        element_key = f"{element_id}:{element_name}:{element_type}"
        value = event_data.get('value', '')
        
        structured_element = {
            'id': element_id,
            'name': element_name,
            'type': element_type,
            'label': element_info.get('label', '')
        }
        
        action = self.action_converter.finalize_input(element_key)
        if action:
            self.yaml_writer.add_step(action)
            value_preview = action.get('text', '')
            
            # Log with structured logger
            if self.recorder_logger:
                self.recorder_logger.log_user_action(
                    action_type='type',
                    element_info=structured_element,
                    success=True,
                    details={'value_preview': value_preview[:50], 'action_description': action.get('description', '')}
                )
            else:
                logger.info(f"Input finalized on blur: {action.get('description', '')} = '{value_preview[:50]}'")
        else:
            # Log if no action was created (no pending input found)
            if self.recorder_logger:
                self.recorder_logger.log_user_action(
                    action_type='type',
                    element_info=structured_element,
                    success=False,
                    error=f"No pending input found for {element_key}",
                    warnings=[f"Pending inputs: {list(self.action_converter.pending_inputs.keys())}"]
                )
            else:
                logger.warning(f"No pending input found for element_key={element_key}")
    
    def handle_navigation(self, event_data: dict) -> None:
        """Handle navigation event."""
        if not self.is_recording or self.is_paused:
            # Log handler skipped
            if self.recorder_logger and self.recorder_logger.is_debug:
                self.recorder_logger.log_screen_event(
                    event_type='handler_skipped',
                    page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                    details={'handler': 'handle_navigation', 'reason': 'not_recording' if not self.is_recording else 'paused'}
                )
            return
        
        url = event_data.get('url', '')
        previous_url = event_data.get('previous_url', '')
        
        # Skip if it's the initial URL (already added)
        if url == self.action_converter.initial_url:
            logger.debug(f"Skipping navigation to initial URL: {url}")
            return
        
        # CRITICAL: Finalize all pending inputs BEFORE clearing on navigation
        # This ensures inputs are captured even if blur wasn't received (e.g., submit button clicked)
        if self.action_converter.pending_inputs:
            if self.recorder_logger:
                self.recorder_logger.log_screen_event(
                    event_type='navigation',
                    page_state={'url': url, 'previous_url': previous_url},
                    details={'pending_inputs_count': len(self.action_converter.pending_inputs)}
                )
            
            for element_key in list(self.action_converter.pending_inputs.keys()):
                action = self.action_converter.finalize_input(element_key)
                if action:
                    self.yaml_writer.add_step(action)
                    value_preview = action.get('text', '')
                    
                    if self.recorder_logger:
                        self.recorder_logger.log_user_action(
                            action_type='type',
                            success=True,
                            details={'value_preview': value_preview[:50], 'finalized_on': 'navigation'}
                        )
                    else:
                        logger.info(f"Finalized input on navigation: {action.get('description', '')} = '{value_preview[:50]}'")
            # Clear after finalizing
            self.action_converter.pending_inputs.clear()
        
        # Skip all navigations - they're caused by clicks which are already captured as 'click' actions
        # Only the initial URL is recorded (done in start())
        logger.debug(f"Skipping navigation from {previous_url} to {url} (click already captured)")
    
    def handle_scroll(self, event_data: dict) -> None:
        """Handle scroll event."""
        if not self.is_recording or self.is_paused:
            # Log handler skipped
            if self.recorder_logger and self.recorder_logger.is_debug:
                self.recorder_logger.log_screen_event(
                    event_type='handler_skipped',
                    page_state={'url': self.page.url if hasattr(self.page, 'url') else 'N/A'},
                    details={'handler': 'handle_navigation', 'reason': 'not_recording' if not self.is_recording else 'paused'}
                )
            return
        
        action = self.action_converter.convert_scroll(event_data)
        if action:
            self.yaml_writer.add_step(action)
            
            if self.recorder_logger:
                self.recorder_logger.log_user_action(
                    action_type='scroll',
                    success=True,
                    details={'action_description': action.get('description', '')}
                )
            else:
                logger.info(f"Scroll action added: {action.get('description', '')}")

