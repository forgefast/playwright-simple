#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write mode operations.

Provides helper functions for write mode operations like handling keydown events
and finding submit buttons.
"""

import logging
from typing import Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def find_submit_button(page: Page, context_element: dict) -> Optional[Dict[str, Any]]:
    """
    Try to find a submit button on the page.
    Queries the page for common submit button patterns.
    
    Args:
        page: Playwright Page instance
        context_element: Context element dictionary (currently unused but kept for compatibility)
        
    Returns:
        Dictionary with action, text, and description if button found, None otherwise
    """
    if not page:
        return None
    
    try:
        # Query page for submit buttons
        buttons = await page.evaluate("""
            () => {
                const buttons = [];
                // Find all buttons and inputs with type submit
                document.querySelectorAll('button[type="submit"], input[type="submit"], button:not([type]), button[type="button"]').forEach(btn => {
                    const text = (btn.textContent || btn.value || btn.getAttribute('aria-label') || '').trim().toLowerCase();
                    if (text && text.length < 50) {
                        buttons.push({
                            text: text,
                            fullText: (btn.textContent || btn.value || '').trim(),
                            tagName: btn.tagName,
                            type: btn.type || '',
                            id: btn.id || '',
                            name: btn.name || ''
                        });
                    }
                });
                return buttons;
            }
        """)
        
        # Look for common submit button texts
        submit_keywords = ['entrar', 'login', 'submit', 'enviar', 'confirmar', 'salvar', 'save', 'log in', 'sign in']
        
        for button in buttons:
            button_text_lower = button.get('text', '').lower()
            if any(keyword in button_text_lower for keyword in submit_keywords):
                # Found a submit button
                full_text = button.get('fullText', '')
                if full_text:
                    return {
                        'action': 'click',
                        'text': full_text,
                        'description': f"Clicar em '{full_text}'"
                    }
        
        return None
    except Exception as e:
        logger.debug(f"Error finding submit button: {e}")
        return None


async def handle_keydown_event(
    event_data: dict,
    action_converter,
    yaml_writer,
    page: Page,
    is_recording: bool,
    is_paused: bool,
    debug: bool = False
) -> None:
    """
    Handle keydown event during write mode recording.
    
    Args:
        event_data: Keydown event data dictionary
        action_converter: ActionConverter instance
        yaml_writer: YAMLWriter instance
        page: Playwright Page instance
        is_recording: Whether recording is active
        is_paused: Whether recording is paused
        debug: Enable debug logging
    """
    if not is_recording or is_paused:
        if debug:
            logger.info(f"🔍 DEBUG: Keydown ignored - is_recording: {is_recording}, is_paused: {is_paused}")
        return
    
    if debug:
        logger.info(f"🔍 DEBUG: Handling keydown event: {event_data}")
    
    result = action_converter.convert_keydown(event_data)
    
    if not result:
        return
    
    # Handle special return types from convert_keydown
    if isinstance(result, dict) and result.get('type') == 'input_finalized':
        # Finalize input first
        input_action = result.get('input_action')
        if input_action:
            yaml_writer.add_step(input_action)
            value_preview = input_action.get('text', '')[:50]
            if len(input_action.get('text', '')) > 50:
                value_preview += '...'
            logger.info(f"Added finalized input step: {input_action.get('description', '')} = '{value_preview}'")
            print(f"📝 Type: {input_action.get('description', '')} = '{value_preview}'")
        
        # Then try to find submit button instead of using Enter
        element_info = result.get('element', {})
        submit_action = await find_submit_button(page, element_info)
        if submit_action:
            yaml_writer.add_step(submit_action)
            logger.info(f"Added submit button click: {submit_action.get('description', '')}")
            print(f"📝 Click: {submit_action.get('description', '')}")
        else:
            # Fallback to Enter if no button found
            enter_action = {
                'action': 'press',
                'key': 'Enter',
                'description': "Pressionar Enter"
            }
            yaml_writer.add_step(enter_action)
            print(f"📝 Key: {enter_action.get('description', '')}")
    
    elif isinstance(result, dict) and result.get('type') == 'enter_pressed':
        # Just Enter, try to find button
        element_info = result.get('element', {})
        submit_action = await find_submit_button(page, element_info)
        if submit_action:
            yaml_writer.add_step(submit_action)
            logger.info(f"Added submit button click: {submit_action.get('description', '')}")
            print(f"📝 Click: {submit_action.get('description', '')}")
        else:
            enter_action = {
                'action': 'press',
                'key': 'Enter',
                'description': "Pressionar Enter"
            }
            yaml_writer.add_step(enter_action)
            print(f"📝 Key: {enter_action.get('description', '')}")
    
    elif isinstance(result, dict) and 'action' in result:
        # Regular action (Tab finalizes input, Escape, etc.)
        yaml_writer.add_step(result)
        print(f"📝 Key: {result.get('description', '')}")

