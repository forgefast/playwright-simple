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
    
    def __init__(self, recorder_logger=None):
        """Initialize action converter."""
        self.last_input_value = None
        self.last_input_element = None
        self.pending_inputs: Dict[str, Dict[str, Any]] = {}  # Track pending inputs by element key
        self.initial_url = None  # Store initial URL
        self._last_click = {}  # Track last click to filter duplicates
        self._recent_clicks = []  # Track recent clicks (last 5) for better duplicate detection
        self.recorder_logger = recorder_logger
    
    def convert_click(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert click event to YAML action.
        All clicks are converted to 'click' action, never 'go_to'.
        Submit buttons are converted to 'submit' action.
        
        Filters out duplicate clicks on the same element within a short time window.
        
        IMPORTANT: This should ALWAYS return an action if element_info exists.
        If element_info is missing, return None (event is invalid).
        
        Args:
            event_data: Click event data
            
        Returns:
            YAML action dictionary or None (only if element_info is missing)
        """
        element_info = event_data.get('element', {})
        if not element_info:
            logger.warning("convert_click: No element_info in event_data")
            return None
        
        # Filter duplicate clicks on the same element within 500ms
        # This prevents capturing rapid duplicate clicks, but allows clicks on different elements
        element_id = element_info.get('id', '')
        element_name = element_info.get('name', '')
        element_tag = element_info.get('tagName', '').upper()
        # Also use placeholder and type to better identify input fields
        element_placeholder = element_info.get('placeholder', '')
        element_type = element_info.get('type', '')
        # Get label text to detect label->input clicks
        label_text = element_info.get('label', '')
        
        # Create a more specific key for input fields
        # Also include text in the key to better identify elements
        element_text = (element_info.get('text', '') or element_info.get('value', '') or '').strip()[:50]
        if element_tag == 'INPUT':
            element_key = f"{element_tag}:{element_id}:{element_name}:{element_placeholder}:{element_type}"
        else:
            # For non-inputs, include text in key for better identification
            element_key = f"{element_tag}:{element_id}:{element_name}:{element_text}"
        timestamp = event_data.get('timestamp', 0)
        
        # Check if this is a duplicate click on the same element
        # Check against all recent clicks (not just the last one) for better duplicate detection
        current_href = element_info.get('href', '')
        current_text = element_text.strip().lower()
        
        # Check all recent clicks
        for recent_click in self._recent_clicks:
            last_key = recent_click.get('key', '')
            last_tag = recent_click.get('tag', '')
            last_timestamp = recent_click.get('timestamp', 0)
            last_href = recent_click.get('href', '')
            last_text = recent_click.get('text', '').strip().lower()
            time_diff = timestamp - last_timestamp
            
            # Only check clicks within 2000ms window
            if time_diff >= 2000:
                continue
            
            # Check multiple ways to identify same element:
            # 1. Same key (most reliable)
            # 2. Same href (for links)
            # 3. Same text and tag (for elements without id/name)
            is_same_element = (
                last_key == element_key or
                (current_href and last_href == current_href) or
                (current_text and last_text == current_text and last_tag == element_tag and not element_id and not element_name)
            )
            
            if is_same_element:
                logger.info(f"🔄 Filtering duplicate click: key={element_key}, text='{element_text}', href='{current_href}', time_diff={time_diff}ms (matched with recent click)")
                
                # Log action filtered
                if self.recorder_logger and self.recorder_logger.is_debug:
                    self.recorder_logger.log_screen_event(
                        event_type='action_filtered',
                        page_state=None,
                        details={'reason': 'duplicate_click', 'element_key': element_key, 'element_text': element_text, 'time_diff_ms': time_diff}
                    )
                
                return None  # Ignore duplicate click
            
            # CRITICAL: Filter clicks on INPUT that happen right after a click on LABEL
            # When you click a label, it automatically focuses/clicks the associated input
            # So we should ignore the input click if it happens within 300ms of a label click
            if (last_tag == 'LABEL' and element_tag == 'INPUT' and time_diff < 300):
                # Check if this input is associated with the label
                # The label text should match the input's label or the input should have the label's 'for' attribute
                last_text = self._last_click.get('text', '').lower()
                # If label text matches input label or input name/id, it's likely the associated input
                if (label_text and last_text in label_text.lower()) or \
                   (element_name and last_text in element_name.lower()) or \
                   (element_id and last_text in element_id.lower()):
                    logger.debug(f"Filtering input click after label click: label='{last_text}', input='{element_name or element_id}' within {time_diff}ms")
                    
                    # Log action filtered
                    if self.recorder_logger and self.recorder_logger.is_debug:
                        self.recorder_logger.log_screen_event(
                            event_type='action_filtered',
                            page_state=None,
                            details={'reason': 'input_after_label_click', 'label_text': last_text, 'input_name': element_name or element_id, 'time_diff_ms': time_diff}
                        )
                    
                    return None  # Ignore input click caused by label click
        
        # Store this click (include tag and text for label->input detection)
        # Also store href for links to better identify duplicates
        click_data = {
            'key': element_key,
            'tag': element_tag,
            'text': element_info.get('text', '') or element_info.get('label', '') or element_info.get('value', ''),
            'href': element_info.get('href', ''),
            'timestamp': timestamp
        }
        self._last_click = click_data
        
        # Add to recent clicks list (keep last 5)
        self._recent_clicks.append(click_data)
        if len(self._recent_clicks) > 5:
            self._recent_clicks.pop(0)
        
        # Check if this is a submit button
        element_type = element_info.get('type', '').lower()
        tag_name = element_info.get('tagName', '').upper()
        text = (element_info.get('text', '') or element_info.get('value', '') or '').lower()
        href = element_info.get('href', '') or ''
        is_link = tag_name == 'A' and bool(href)
        is_in_form = element_info.get('isInForm', False)
        
        # IMPORTANT: Links (href) should ALWAYS be treated as 'click', never 'submit'
        # Even if they look like buttons to the user, they are navigation links
        # Only actual buttons can be submit buttons
        # A button is a submit button if:
        # 1. It has type="submit" explicitly, OR
        # 2. It's a BUTTON tag inside a form (default behavior is submit), OR
        # 3. It's an INPUT with type="submit"
        is_submit_button = (
            element_type == 'submit' or
            (tag_name == 'BUTTON' and (element_type in ('submit', '') or is_in_form)) or
            (tag_name == 'INPUT' and element_type == 'submit')
        )
        # Links are never submit buttons, they are always clicks
        
        # Identify element
        identification = ElementIdentifier.identify(element_info)
        
        # Ensure we always have a valid description
        if not identification.get('description'):
            # Fallback description if identification failed
            tag_name = element_info.get('tagName', 'element').lower()
            text = element_info.get('text', '').strip()
            href = element_info.get('href', '')
            if text:
                # For links, add context to differentiate from buttons
                if is_link:
                    # Check if link is in header/nav (common pattern)
                    className = element_info.get('className', '').lower()
                    if 'header' in className or 'nav' in className or 'menu' in className:
                        description = f"Clicar em '{text}' (link no header)"
                    else:
                        description = f"Clicar em '{text}' (link)"
                else:
                    description = f"Clicar em '{text}'"
            elif href:
                description = f"Clicar em link ({href})"
            else:
                description = f"Clicar em {tag_name}"
            identification['description'] = description
        
        if is_submit_button:
            # Convert to submit action
            action = {
                'action': 'submit',
                'description': f"Submeter formulário: {identification['description']}"
            }
            
            if identification.get('text'):
                action['button_text'] = identification['text']
            elif identification.get('selector'):
                action['selector'] = identification['selector']
            # If no text or selector, still create action (description is enough)
        else:
            # Convert to click action (this includes all links)
            action = {
                'action': 'click',
                'description': identification['description']
            }
            
            if identification.get('text'):
                action['text'] = identification['text']
            elif identification.get('selector'):
                action['selector'] = identification['selector']
            # If no text or selector, still create action (description is enough)
            # For links, try to use href as fallback
            if not action.get('text') and not action.get('selector'):
                href = element_info.get('href', '')
                if href:
                    action['selector'] = f"a[href='{href}']"
            
            # For links in header/nav, we can add context to description if needed
            # But the action is always 'click', never 'submit'
        
        # ALWAYS return an action if we got here (element_info exists)
        logger.debug(f"convert_click: Created action - {action.get('action')}: {action.get('description')}")
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
        
        # Add field_text if we have label or placeholder (for CursorController to find field)
        # If we have label/placeholder, CursorController can find the field by text
        label = ElementIdentifier._get_label(element_info)
        placeholder = ElementIdentifier._get_placeholder(element_info)
        
        if label:
            # Use label as field_text so CursorController can find it
            action['field_text'] = label
        elif placeholder:
            # Use placeholder as field_text so CursorController can find it
            action['field_text'] = placeholder
        
        if not label and not placeholder:
            # No label or placeholder, add selector as fallback
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
            action = None
            if event_type == 'click':
                action = self.convert_click(event_data)
            elif event_type == 'input':
                action = self.convert_input(event_data)
            elif event_type == 'navigation':
                action = self.convert_navigation(event_data)
            elif event_type == 'scroll':
                action = self.convert_scroll(event_data)
            elif event_type == 'keydown':
                action = self.convert_keydown(event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                # Log unknown event type
                if self.recorder_logger:
                    self.recorder_logger.warning(
                        message=f"Unknown event type: {event_type}",
                        details={'event_data': event_data}
                    )
                return None
            
            # Log event converted (only in debug mode to avoid spam)
            if self.recorder_logger and self.recorder_logger.is_debug and action:
                element_info = event_data.get('element', {})
                self.recorder_logger.log_screen_event(
                    event_type='event_converted',
                    page_state=None,
                    details={'event_type': event_type, 'action_type': action.get('action'), 'element_text': element_info.get('text', '')[:50] if element_info else ''}
                )
            
            return action
        except Exception as e:
            logger.error(f"Error converting event {event_type}: {e}")
            # Log conversion failure
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='convert_event',
                    error=str(e),
                    page_state=None,
                    details={'event_type': event_type, 'event_data': event_data}
                )
            return None

