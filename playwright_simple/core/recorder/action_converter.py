#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action converter module.

Converts captured events into generic YAML actions.
"""

import logging
from typing import Dict, Any, Optional
from .element_identifier import ElementIdentifier

logger = logging.getLogger(__name__)


class ActionConverter:
    """Converts events to YAML actions."""
    
    def __init__(self):
        """Initialize action converter."""
        self.last_input_value = None
        self.last_input_element = None
        self.pending_inputs: Dict[str, Dict[str, Any]] = {}  # Track pending inputs by element key
        self.initial_url = None  # Store initial URL
    
    def convert_click(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert click event to YAML action.
        All clicks are converted to 'click' action, never 'go_to'.
        Submit buttons are converted to 'submit' action.
        
        Args:
            event_data: Click event data
            
        Returns:
            YAML action dictionary or None
        """
        element_info = event_data.get('element', {})
        if not element_info:
            return None
        
        # Check if this is a submit button
        element_type = element_info.get('type', '').lower()
        tag_name = element_info.get('tagName', '').upper()
        text = (element_info.get('text', '') or element_info.get('value', '') or '').lower()
        
        # Links (A tags) should NEVER be converted to submit, even if they have submit-like text
        # They should always be click actions
        is_submit_button = (
            tag_name != 'A' and (  # Links are never submit buttons
                element_type == 'submit' or
                (tag_name == 'BUTTON' and element_type in ('submit', '')) or
                any(keyword in text for keyword in ['entrar', 'login', 'submit', 'enviar', 'salvar', 'save', 'confirmar', 'confirm', 'log in', 'sign in'])
            )
        )
        
        # Identify element
        identification = ElementIdentifier.identify(element_info)
        
        if is_submit_button:
            # Convert to submit action
            action = {
                'action': 'submit',
                'description': f"Submeter formulário: {identification['description']}"
            }
            
            if identification['text']:
                action['button_text'] = identification['text']
            elif identification['selector']:
                action['selector'] = identification['selector']
        else:
            # Convert to click action
            action = {
                'action': 'click',
                'description': identification['description']
            }
            
            if identification['text']:
                action['text'] = identification['text']
            elif identification['selector']:
                action['selector'] = identification['selector']
        
        return action
    
    def convert_input(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert input event to YAML action.
        Accumulates input and only returns action when field loses focus or Enter is pressed.
        
        Args:
            event_data: Input event data
            
        Returns:
            YAML action dictionary or None (None means accumulate, action means finalize)
        """
        element_info = event_data.get('element', {})
        value = event_data.get('value', '')
        
        if not element_info:
            logger.debug("convert_input: No element info")
            return None
        
        # Use a combination of id, name, and type to identify unique inputs
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_type = element_info.get('type', '')
        element_key = f"{element_id}:{element_name}:{element_type}"
        
        # Store pending input (accumulate)
        self.pending_inputs[element_key] = {
            'element': element_info,
            'value': value,
            'timestamp': event_data.get('timestamp')
        }
        
        # Don't return action yet - wait for blur or Enter
        logger.debug(f"convert_input: Accumulating input for {element_key} = '{value[:30]}...'")
        return None
    
    def finalize_input(self, element_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Finalize and return accumulated input action.
        
        Args:
            element_key: Specific element to finalize, or None for all
            
        Returns:
            YAML action dictionary or None
        """
        if element_key:
            pending = self.pending_inputs.pop(element_key, None)
        else:
            # Get the most recent pending input
            if not self.pending_inputs:
                return None
            # Get the last one (most recent)
            element_key = list(self.pending_inputs.keys())[-1]
            pending = self.pending_inputs.pop(element_key)
        
        if not pending:
            return None
        
        element_info = pending['element']
        value = pending['value']
        
        # Identify element
        identification = ElementIdentifier.identify_for_input(element_info, value)
        
        action = {
            'action': 'type',
            'text': value,
            'description': identification['description']
        }
        
        # Add selector if needed (for fallback)
        if identification.get('selector'):
            action['selector'] = identification['selector']
        elif element_info.get('name'):
            action['selector'] = f"[name='{element_info['name']}']"
        elif element_info.get('id'):
            action['selector'] = f"#{element_info['id']}"
        
        logger.debug(f"finalize_input: Created action - {action.get('description')} = '{value[:30]}...'")
        return action
    
    def convert_navigation(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert navigation event to YAML action.
        Navigation is only recorded for initial URL, not for link clicks.
        
        Args:
            event_data: Navigation event data
            
        Returns:
            YAML action dictionary or None
        """
        url = event_data.get('url', '')
        previous_url = event_data.get('previous_url', '')
        
        if not url:
            return None
        
        # Only record initial navigation (when starting recording)
        # Link clicks are already captured as 'click' actions
        if not previous_url or previous_url == 'about:blank':
            # This is the initial navigation - skip it as it's already added in recorder.start()
            return None
        
        # Skip all other navigations - they're caused by clicks which are already recorded
        return None
    
    def convert_scroll(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert scroll event to YAML action.
        
        Args:
            event_data: Scroll event data
            
        Returns:
            YAML action dictionary or None
        """
        scroll_x = event_data.get('scrollX', 0)
        scroll_y = event_data.get('scrollY', 0)
        
        # Determine direction
        if scroll_y > 0:
            direction = 'down'
        elif scroll_y < 0:
            direction = 'up'
        elif scroll_x > 0:
            direction = 'right'
        elif scroll_x < 0:
            direction = 'left'
        else:
            return None
        
        return {
            'action': 'scroll',
            'direction': direction,
            'amount': abs(scroll_y) if scroll_y != 0 else abs(scroll_x),
            'description': f"Rolar página para {direction}"
        }
    
    def convert_keydown(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert keydown event to YAML action.
        
        Args:
            event_data: Keydown event data
            
        Returns:
            YAML action dictionary or None, or list of actions (input finalization + key action)
        """
        key = event_data.get('key', '')
        element_info = event_data.get('element', {})
        
        if key == 'Enter':
            # Enter key - finalize any pending input first
            element_id = element_info.get('id', '')
            element_name = element_info.get('name', '')
            element_type = element_info.get('type', '')
            element_key = f"{element_id}:{element_name}:{element_type}"
            
            # Finalize input if there's a pending one
            input_action = self.finalize_input(element_key)
            
            # Try to find submit button instead of using press Enter
            # Look for button with text like "Entrar", "Login", "Submit", etc.
            # For now, return the input action and let the handler look for button
            if input_action:
                return {
                    'type': 'input_finalized',
                    'input_action': input_action,
                    'key': 'Enter',
                    'element': element_info
                }
            else:
                # No pending input, just Enter - try to find button
                return {
                    'type': 'enter_pressed',
                    'key': 'Enter',
                    'element': element_info
                }
        elif key == 'Tab':
            # Tab key - finalize input and move to next field
            element_id = element_info.get('id', '')
            element_name = element_info.get('name', '')
            element_type = element_info.get('type', '')
            element_key = f"{element_id}:{element_name}:{element_type}"
            
            # Finalize input
            return self.finalize_input(element_key)
        elif key == 'Escape':
            # Escape - clear pending inputs
            self.pending_inputs.clear()
            return {
                'action': 'press',
                'key': 'Escape',
                'description': "Pressionar Escape"
            }
        
        return None
    
    def convert(self, event_type: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert event to YAML action.
        
        Args:
            event_type: Type of event (click, input, navigation, etc.)
            event_data: Event data
            
        Returns:
            YAML action dictionary or None
        """
        try:
            if event_type == 'click':
                return self.convert_click(event_data)
            elif event_type == 'input':
                return self.convert_input(event_data)
            elif event_type == 'navigation':
                return self.convert_navigation(event_data)
            elif event_type == 'scroll':
                return self.convert_scroll(event_data)
            elif event_type == 'keydown':
                return self.convert_keydown(event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None
        except Exception as e:
            logger.error(f"Error converting event {event_type}: {e}")
            return None

